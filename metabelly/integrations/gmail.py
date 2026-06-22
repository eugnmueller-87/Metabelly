"""
Gmail integration.

Flow:
  1. Gmail sends new-email notifications via Google Cloud Pub/Sub
  2. Our /webhook/gmail endpoint receives the push notification
  3. We call Gmail API to fetch the full email
  4. We extract sender + body, encrypt, push to queue

Setup (one-time, done in Google Cloud Console):
  - Enable Gmail API
  - Create Pub/Sub topic + subscription (push to our /webhook/gmail URL)
  - Grant Gmail API watch permission to the inbox
  - Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN in .env
"""

import base64
import email as email_lib
import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from metabelly.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailClient:
    def __init__(self, account_email: str | None = None) -> None:
        """
        Pass account_email to select which inbox to operate on.
        Defaults to the first configured account (gmail_support_email).
        """
        accounts = settings.gmail_accounts()
        if not accounts:
            raise ValueError("No Gmail accounts configured in .env")

        if account_email:
            if account_email not in accounts:
                raise ValueError(f"Gmail account {account_email!r} not found in config")
            account = accounts[account_email]
        else:
            account = next(iter(accounts.values()))

        self._email = account["email"]
        creds = Credentials(
            token=None,
            refresh_token=account["refresh_token"],
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )
        self._service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    @property
    def email(self) -> str:
        return self._email

    def fetch_email(self, message_id: str) -> "ParsedEmail | None":
        try:
            msg = (
                self._service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return _parse_message(msg)
        except HttpError as e:
            logger.error("Failed to fetch Gmail message %s: %s", message_id, e)
            return None

    def send_reply(self, to: str, subject: str, body: str, thread_id: str) -> bool:
        try:
            message = _build_reply(to, subject, body, thread_id)
            self._service.users().messages().send(userId="me", body=message).execute()
            return True
        except HttpError as e:
            logger.error("Failed to send reply to %s: %s", to, e)
            return False

    def renew_watch(self, topic_name: str) -> None:
        """Renew Gmail push watch — expires every 7 days, call weekly."""
        self._service.users().watch(
            userId="me",
            body={"topicName": topic_name, "labelIds": ["INBOX"]},
        ).execute()
        logger.info("Gmail watch renewed for topic %s", topic_name)


class ParsedEmail:
    def __init__(
        self,
        message_id: str,
        thread_id: str,
        sender_email: str,
        subject: str,
        body: str,
    ) -> None:
        self.message_id = message_id
        self.thread_id = thread_id
        self.sender_email = sender_email
        self.subject = subject
        self.body = body

    @property
    def full_text(self) -> str:
        return f"Subject: {self.subject}\n\n{self.body}"


def _parse_message(msg: dict[str, Any]) -> ParsedEmail:
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    sender_raw = headers.get("from", "")
    sender_email = _extract_email(sender_raw)
    subject = headers.get("subject", "(no subject)")
    body = _extract_body(msg["payload"])

    return ParsedEmail(
        message_id=msg["id"],
        thread_id=msg["threadId"],
        sender_email=sender_email,
        subject=subject,
        body=body,
    )


def _extract_email(raw: str) -> str:
    if "<" in raw and ">" in raw:
        return raw.split("<")[1].split(">")[0].strip().lower()
    return raw.strip().lower()


def _extract_body(payload: dict[str, Any]) -> str:
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    if mime_type.startswith("multipart/"):
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    return ""


def _build_reply(to: str, subject: str, body: str, thread_id: str) -> dict[str, str]:
    msg = email_lib.message.EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw, "threadId": thread_id}
