from metabelly.core.config import settings

# Raw SQL — no ORM overhead, no extra abstraction layer
# SQLAlchemy core only when we actually need it

CREATE_QUEUE_TABLE = """
CREATE TABLE IF NOT EXISTS email_queue (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gmail_id        TEXT UNIQUE NOT NULL,
    thread_id       TEXT NOT NULL,
    sender_email    TEXT NOT NULL,
    subject         TEXT NOT NULL DEFAULT '',
    content_encrypted TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','processing','done','failed')),
    attempts        INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '90 days'
);

CREATE INDEX IF NOT EXISTS idx_queue_status ON email_queue (status);
CREATE INDEX IF NOT EXISTS idx_queue_expires ON email_queue (expires_at);
"""

CREATE_TICKET_TABLE = """
CREATE TABLE IF NOT EXISTS tickets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_item_id   UUID NOT NULL REFERENCES email_queue(id),
    category        TEXT NOT NULL,
    priority        TEXT NOT NULL,
    language        TEXT NOT NULL,
    summary         TEXT NOT NULL,
    requires_human  BOOLEAN NOT NULL,
    suggested_action TEXT NOT NULL,
    auto_reply_sent BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets (priority);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets (category);
"""

CLEANUP_EXPIRED = """
DELETE FROM email_queue
WHERE expires_at < now() AND status = 'done';
"""

PICK_NEXT_PENDING = """
UPDATE email_queue
SET status = 'processing', attempts = attempts + 1
WHERE id = (
    SELECT id FROM email_queue
    WHERE status = 'pending'
      AND attempts < 3
    ORDER BY created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
RETURNING *;
"""

MARK_DONE = """
UPDATE email_queue
SET status = 'done', processed_at = now()
WHERE id = $1;
"""

MARK_FAILED = """
UPDATE email_queue
SET status = 'failed'
WHERE id = $1;
"""

RESET_STUCK = """
UPDATE email_queue
SET status = 'pending'
WHERE status = 'processing'
  AND created_at < now() - INTERVAL '10 minutes';
"""
