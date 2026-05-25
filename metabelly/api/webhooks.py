"""
Webhook endpoints.

Gmail Pub/Sub push flow:
  Google → POST /webhook/gmail → decode notification → fetch email → queue it

Google signs Pub/Sub requests with a JWT — we verify the token against
Google's public keys before processing anything.
"""
import base64
import json
import logging

import httpx
from fastapi import APIRouter, Header, HTTPException, Request

from metabelly.api.security import check_email_rate_limit, sanitize_for_llm
from metabelly.core.audit import AuditEvent, Severity, log
from metabelly.integrations.gmail import GmailClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook")

# Google's token info endpoint — used to verify Pub/Sub JWT
_GOOGLE_TOKEN_INFO = "https://oauth2.googleapis.com/tokeninfo"


@router.post("/gmail")
async def gmail_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    client_ip = _get_ip(request)

    # Step 1 — verify Google signed this request
    await _verify_google_jwt(authorization, client_ip)

    # Step 2 — decode the Pub/Sub envelope
    body = await request.json()
    message_id, gmail_message_id = _decode_pubsub(body)

    log(AuditEvent.WEBHOOK_RECEIVED, ip=client_ip, detail=f"pubsub_msg={message_id}")

    # Step 3 — fetch full email from Gmail API
    gmail = GmailClient()
    parsed = gmail.fetch_email(gmail_message_id)

    if not parsed:
        logger.warning("Could not fetch Gmail message %s", gmail_message_id)
        return {"status": "skipped"}

    # Step 4 — rate limit per sender
    check_email_rate_limit(parsed.sender_email, client_ip)

    # Step 5 — sanitize content before it touches the LLM
    safe_content = sanitize_for_llm(parsed.full_text, client_ip)

    # Step 6 — push to queue (imported here to avoid circular deps)
    from metabelly.core.queue_service import enqueue  # noqa: PLC0415

    await enqueue(
        gmail_id=parsed.message_id,
        thread_id=parsed.thread_id,
        sender_email=parsed.sender_email,
        subject=parsed.subject,
        content=safe_content,
    )

    log(AuditEvent.EMAIL_QUEUED, ip=client_ip, detail=f"gmail_id={parsed.message_id[:8]}***")
    return {"status": "queued"}


async def _verify_google_jwt(authorization: str | None, client_ip: str) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        log(AuditEvent.SIGNATURE_INVALID, Severity.ERROR, ip=client_ip,
            detail="missing bearer token")
        raise HTTPException(status_code=401, detail="Missing authorization")

    token = authorization.removeprefix("Bearer ")

    async with httpx.AsyncClient() as client:
        resp = await client.get(_GOOGLE_TOKEN_INFO, params={"id_token": token})

    if resp.status_code != 200:
        log(AuditEvent.SIGNATURE_INVALID, Severity.ERROR, ip=client_ip,
            detail="invalid google jwt")
        raise HTTPException(status_code=401, detail="Invalid Google token")


def _decode_pubsub(body: dict) -> tuple[str, str]:
    """Extract Pub/Sub message ID and the Gmail message ID from the payload."""
    try:
        pubsub_message = body["message"]
        message_id: str = pubsub_message["messageId"]
        data = json.loads(base64.b64decode(pubsub_message["data"]).decode())
        gmail_message_id: str = data["message"]["data"]["messageId"] if "message" in data else data["messageId"]
        return message_id, gmail_message_id
    except (KeyError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub payload") from e


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
