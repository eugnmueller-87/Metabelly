import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from metabelly.api.security import security_middleware
from metabelly.api.webhooks import router as webhook_router
from metabelly.core.config import settings

logger = logging.getLogger(__name__)

WATCH_RENEWAL_INTERVAL = 6 * 24 * 60 * 60  # 6 days — Gmail watch expires every 7


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    tasks: list[asyncio.Task] = []

    if settings.database_url:
        from metabelly.core.db_pool import close_pool, init_pool
        await init_pool()
        logger.info("Database pool ready")

        from metabelly.agents.classifier import TriageClassifier
        from metabelly.core.dispatcher import Dispatcher
        from metabelly.core.worker import QueueWorker

        dispatcher = Dispatcher()
        classifier = TriageClassifier()

        from metabelly.core.db_pool import pool
        async with pool.acquire() as conn:
            worker = QueueWorker(
                db=conn,
                classifier=classifier,
                on_result=lambda gid, email, subj, tid, result, qid: dispatcher.handle(
                    gmail_id=gid,
                    sender_email=email,
                    subject=subj,
                    thread_id=tid,
                    result=result,
                    queue_item_id=qid,
                ),
            )

        tasks.append(asyncio.create_task(worker.start()))
        tasks.append(asyncio.create_task(_watch_renewal_loop()))
        logger.info("Worker and watch renewal started")

    yield

    for task in tasks:
        task.cancel()

    if settings.database_url:
        from metabelly.core.db_pool import close_pool
        await close_pool()

    logger.info("Shutdown complete")


async def _watch_renewal_loop() -> None:
    while True:
        await asyncio.sleep(WATCH_RENEWAL_INTERVAL)
        try:
            from metabelly.integrations.gmail import GmailClient
            GmailClient().renew_watch(settings.google_pubsub_topic)
            logger.info("Gmail watch renewed")
        except Exception:
            logger.exception("Gmail watch renewal failed")


app = FastAPI(
    title="Metabelly Triage API",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.middleware("http")(security_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_methods=["POST"],
)

app.include_router(webhook_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
