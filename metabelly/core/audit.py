"""
Append-only audit log. Every security-relevant event is recorded.
Stored in DB — never deleted, never updated.
"""
import logging
from datetime import datetime, timezone
from enum import Enum
from ipaddress import ip_address

logger = logging.getLogger("metabelly.audit")

CREATE_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event       TEXT NOT NULL,
    severity    TEXT NOT NULL,
    ip          TEXT,
    detail      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_event    ON audit_log (event);
CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_log (severity);
CREATE INDEX IF NOT EXISTS idx_audit_created  ON audit_log (created_at);
"""


class AuditEvent(str, Enum):
    # Auth
    WEBHOOK_RECEIVED      = "webhook_received"
    SIGNATURE_INVALID     = "signature_invalid"
    SIGNATURE_REPLAY      = "signature_replay"
    IP_BLOCKED            = "ip_blocked"

    # Rate limiting
    RATE_LIMIT_IP         = "rate_limit_ip"
    RATE_LIMIT_EMAIL      = "rate_limit_email"

    # Payload
    PAYLOAD_TOO_LARGE     = "payload_too_large"
    INJECTION_DETECTED    = "injection_detected"

    # Processing
    EMAIL_QUEUED          = "email_queued"
    EMAIL_DUPLICATE       = "email_duplicate"
    EMAIL_CLASSIFIED      = "email_classified"
    AUTO_REPLY_SENT       = "auto_reply_sent"
    EMAIL_FAILED          = "email_failed"
    EMAIL_PERMANENTLY_FAILED = "email_permanently_failed"

    # System
    WORKER_STARTED        = "worker_started"
    WORKER_STOPPED        = "worker_stopped"
    STUCK_ITEMS_RESET     = "stuck_items_reset"


class Severity(str, Enum):
    INFO    = "info"
    WARNING = "warning"
    ERROR   = "error"
    CRITICAL = "critical"


def log(
    event: AuditEvent,
    severity: Severity = Severity.INFO,
    ip: str | None = None,
    detail: str | None = None,
) -> None:
    logger.log(
        _to_log_level(severity),
        "[AUDIT] event=%s severity=%s ip=%s detail=%s ts=%s",
        event.value,
        severity.value,
        ip or "-",
        detail or "-",
        datetime.now(timezone.utc).isoformat(),
    )


def _to_log_level(severity: Severity) -> int:
    return {
        Severity.INFO:     logging.INFO,
        Severity.WARNING:  logging.WARNING,
        Severity.ERROR:    logging.ERROR,
        Severity.CRITICAL: logging.CRITICAL,
    }[severity]
