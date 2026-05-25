"""
Security middleware and guards.

Layers (applied in order):
  1. IP allowlist          — only known sources reach webhook endpoints
  2. Payload size cap      — blocks token cost attacks
  3. IP rate limit         — max 5 req/min per IP
  4. Email rate limit      — max 3 req/hour per sender
  5. Webhook signature     — HMAC-SHA256, rejects replays > 5min old
  6. Prompt injection      — strips LLM manipulation attempts before classify
  7. Security headers      — HSTS, no-sniff, no-frame, CSP
"""

import hashlib
import hmac
import ipaddress
import re
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request
from fastapi.responses import Response

from metabelly.core.audit import AuditEvent, Severity, log
from metabelly.core.config import settings

# ── Constants ────────────────────────────────────────────────────────────────

MAX_PAYLOAD_BYTES = 10_000
RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_EMAIL_REQUESTS_PER_HOUR = 3
REPLAY_WINDOW_SECONDS = 300

_INJECTION_PATTERN = re.compile(
    r"(ignore\s+(previous|all|above|instructions)|you\s+are\s+now|"
    r"new\s+instruction|system\s+prompt|forget\s+everything|"
    r"pretend\s+you\s+are|jailbreak|disregard\s+(all|previous))",
    re.IGNORECASE,
)

# in-memory stores — sufficient for single instance
_ip_windows: dict[str, list[float]] = defaultdict(list)
_email_windows: dict[str, list[float]] = defaultdict(list)

# ── Security headers ─────────────────────────────────────────────────────────

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# ── Middleware ───────────────────────────────────────────────────────────────


async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    client_ip = _get_ip(request)

    _check_ip_allowlist(client_ip, request.url.path)
    _check_payload_size(request, client_ip)
    _check_ip_rate_limit(client_ip)

    response = await call_next(request)

    for header, value in _SECURITY_HEADERS.items():
        response.headers[header] = value

    return response


# ── IP allowlist ─────────────────────────────────────────────────────────────


def _check_ip_allowlist(client_ip: str, path: str) -> None:
    allowlist = settings.webhook_ip_allowlist
    if not allowlist or not path.startswith("/webhook"):
        return

    try:
        addr = ipaddress.ip_address(client_ip)
        for entry in allowlist:
            network = ipaddress.ip_network(entry, strict=False)
            if addr in network:
                return
    except ValueError:
        pass

    log(AuditEvent.IP_BLOCKED, Severity.WARNING, ip=client_ip, detail=path)
    raise HTTPException(status_code=403, detail="Forbidden")


# ── Payload size ─────────────────────────────────────────────────────────────


def _check_payload_size(request: Request, client_ip: str) -> None:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_PAYLOAD_BYTES:
        log(AuditEvent.PAYLOAD_TOO_LARGE, Severity.WARNING, ip=client_ip)
        raise HTTPException(status_code=413, detail="Payload too large")


# ── IP rate limit ─────────────────────────────────────────────────────────────


def _check_ip_rate_limit(client_ip: str) -> None:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    _ip_windows[client_ip] = [t for t in _ip_windows[client_ip] if t > window_start]

    if len(_ip_windows[client_ip]) >= RATE_LIMIT_REQUESTS:
        log(AuditEvent.RATE_LIMIT_IP, Severity.WARNING, ip=client_ip)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    _ip_windows[client_ip].append(now)


# ── Per-email rate limit ──────────────────────────────────────────────────────


def check_email_rate_limit(sender_email: str, client_ip: str = "") -> None:
    now = time.time()
    window_start = now - 3600
    _email_windows[sender_email] = [t for t in _email_windows[sender_email] if t > window_start]

    if len(_email_windows[sender_email]) >= MAX_EMAIL_REQUESTS_PER_HOUR:
        log(
            AuditEvent.RATE_LIMIT_EMAIL,
            Severity.WARNING,
            ip=client_ip,
            detail=f"sender={sender_email[:6]}***",
        )
        raise HTTPException(status_code=429, detail="Too many requests from this address")

    _email_windows[sender_email].append(now)


# ── Webhook signature verification ───────────────────────────────────────────


def verify_slack_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    client_ip: str = "",
) -> None:
    try:
        age = abs(time.time() - float(timestamp))
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid timestamp") from e

    if age > REPLAY_WINDOW_SECONDS:
        log(AuditEvent.SIGNATURE_REPLAY, Severity.WARNING, ip=client_ip)
        raise HTTPException(status_code=401, detail="Request too old")

    expected = (
        "v0="
        + hmac.new(
            settings.slack_signing_secret.encode(),
            f"v0:{timestamp}:{body.decode()}".encode(),
            hashlib.sha256,
        ).hexdigest()
    )

    if not hmac.compare_digest(expected, signature):
        log(AuditEvent.SIGNATURE_INVALID, Severity.ERROR, ip=client_ip)
        raise HTTPException(status_code=401, detail="Invalid signature")


# ── Prompt injection guard ────────────────────────────────────────────────────


def sanitize_for_llm(text: str, client_ip: str = "") -> str:
    cleaned, count = _INJECTION_PATTERN.subn("[removed]", text)
    if count:
        log(
            AuditEvent.INJECTION_DETECTED,
            Severity.WARNING,
            ip=client_ip,
            detail=f"{count} pattern(s) removed",
        )
    return cleaned[:MAX_PAYLOAD_BYTES]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
