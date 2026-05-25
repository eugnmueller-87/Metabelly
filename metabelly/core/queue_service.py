"""
Thin service layer — inserts emails into the queue table.
Handles deduplication via gmail_id unique constraint.
"""
import logging

from metabelly.core.audit import AuditEvent, Severity, log
from metabelly.core.encryption import encrypt

logger = logging.getLogger(__name__)

INSERT_EMAIL = """
INSERT INTO email_queue (gmail_id, sender_email, content_encrypted)
VALUES ($1, $2, $3)
ON CONFLICT (gmail_id) DO NOTHING
RETURNING id;
"""


async def enqueue(gmail_id: str, sender_email: str, content: str) -> bool:
    """
    Returns True if queued, False if duplicate (already seen this gmail_id).
    Caller must pass a sanitized, truncated content string.
    """
    from metabelly.core.db_pool import pool  # imported lazily — pool created at startup

    encrypted = encrypt(content)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(INSERT_EMAIL, gmail_id, sender_email, encrypted)

    if row is None:
        log(AuditEvent.EMAIL_DUPLICATE, Severity.INFO,
            detail=f"gmail_id={gmail_id[:8]}***")
        return False

    return True
