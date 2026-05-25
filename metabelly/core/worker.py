import asyncio
import logging
from collections.abc import Awaitable, Callable

import asyncpg

from metabelly.agents.classifier import TriageClassifier
from metabelly.core.audit import AuditEvent, Severity, log
from metabelly.core.database import MARK_DONE, MARK_FAILED, PICK_NEXT_PENDING, RESET_STUCK
from metabelly.core.encryption import decrypt
from metabelly.core.models import TriageResult

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
POLL_INTERVAL = 10

# on_result receives all context needed for the Dispatcher
OnResult = Callable[[str, str, str, str, TriageResult, str], Awaitable[None]]


class QueueWorker:
    def __init__(
        self,
        db: asyncpg.Connection,
        classifier: TriageClassifier,
        on_result: OnResult,
    ) -> None:
        self._db = db
        self._classifier = classifier
        self._on_result = on_result
        self._running = False

    async def start(self) -> None:
        self._running = True
        log(AuditEvent.WORKER_STARTED)
        logger.info("Queue worker started")
        while self._running:
            await self._reset_stuck()
            processed = await self._process_next()
            if not processed:
                await asyncio.sleep(POLL_INTERVAL)

    async def stop(self) -> None:
        self._running = False
        log(AuditEvent.WORKER_STOPPED)
        logger.info("Queue worker stopped")

    async def _process_next(self) -> bool:
        row = await self._db.fetchrow(PICK_NEXT_PENDING)
        if not row:
            return False

        item_id: str = str(row["id"])
        gmail_id: str = row["gmail_id"]
        thread_id: str = row["thread_id"]
        sender_email: str = row["sender_email"]
        subject: str = row["subject"]
        attempts: int = row["attempts"]

        logger.info("Processing queue item %s (attempt %d)", item_id, attempts)

        try:
            content = decrypt(row["content_encrypted"])
            result = self._classifier.classify(content)
            await self._on_result(gmail_id, sender_email, subject, thread_id, result, item_id)
            await self._db.execute(MARK_DONE, item_id)
            log(AuditEvent.EMAIL_CLASSIFIED, detail=f"item={item_id[:8]}*** {result.category} {result.priority}")
            logger.info("Item %s done — %s %s", item_id, result.category, result.priority)
        except Exception:
            logger.exception("Item %s failed on attempt %d", item_id, attempts)
            if attempts >= MAX_ATTEMPTS:
                await self._db.execute(MARK_FAILED, item_id)
                log(AuditEvent.EMAIL_PERMANENTLY_FAILED, Severity.ERROR, detail=f"item={item_id[:8]}***")
            else:
                await self._db.execute(
                    "UPDATE email_queue SET status = 'pending' WHERE id = $1", item_id
                )

        return True

    async def _reset_stuck(self) -> None:
        reset = await self._db.execute(RESET_STUCK)
        if reset and reset != "UPDATE 0":
            log(AuditEvent.STUCK_ITEMS_RESET, detail=reset)
