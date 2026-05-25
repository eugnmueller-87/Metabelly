import asyncio
import logging
from collections.abc import Awaitable, Callable

import asyncpg

from metabelly.agents.classifier import TriageClassifier
from metabelly.core.database import MARK_DONE, MARK_FAILED, PICK_NEXT_PENDING, RESET_STUCK
from metabelly.core.encryption import decrypt
from metabelly.core.models import TriageResult

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
POLL_INTERVAL = 10


class QueueWorker:
    def __init__(
        self,
        db: asyncpg.Connection,
        classifier: TriageClassifier,
        on_result: Callable[[str, TriageResult], Awaitable[None]],
    ) -> None:
        self._db = db
        self._classifier = classifier
        self._on_result = on_result
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("Queue worker started")
        while self._running:
            await self._reset_stuck()
            processed = await self._process_next()
            if not processed:
                await asyncio.sleep(POLL_INTERVAL)

    async def stop(self) -> None:
        self._running = False
        logger.info("Queue worker stopped")

    async def _process_next(self) -> bool:
        row = await self._db.fetchrow(PICK_NEXT_PENDING)
        if not row:
            return False

        item_id: str = str(row["id"])
        gmail_id: str = row["gmail_id"]
        attempts: int = row["attempts"]

        logger.info("Processing queue item %s (attempt %d)", item_id, attempts)

        try:
            content = decrypt(row["content_encrypted"])
            result = self._classifier.classify(content)
            await self._on_result(gmail_id, result)
            await self._db.execute(MARK_DONE, item_id)
            logger.info("Item %s done — %s %s", item_id, result.category, result.priority)
        except Exception:
            logger.exception("Item %s failed on attempt %d", item_id, attempts)
            if attempts >= MAX_ATTEMPTS:
                await self._db.execute(MARK_FAILED, item_id)
                logger.error("Item %s permanently failed after %d attempts", item_id, MAX_ATTEMPTS)
            else:
                await self._db.execute(
                    "UPDATE email_queue SET status = 'pending' WHERE id = $1", item_id
                )

        return True

    async def _reset_stuck(self) -> None:
        await self._db.execute(RESET_STUCK)
