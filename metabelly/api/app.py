import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from metabelly.api.security import security_middleware
from metabelly.api.webhooks import router as webhook_router
from metabelly.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.database_url:
        from metabelly.core.db_pool import init_pool, close_pool
        await init_pool()
        logger.info("Database pool ready")
        yield
        await close_pool()
    else:
        yield  # dev mode without DB


app = FastAPI(
    title="Metabelly Triage API",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.middleware("http")(security_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],   # no browser access — webhooks only
    allow_methods=["POST"],
)

app.include_router(webhook_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
