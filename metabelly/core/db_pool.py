"""
Database connection pool — created once at app startup, shared everywhere.
Import `pool` anywhere you need a DB connection.
"""

import asyncpg

from metabelly.core.config import settings

pool: asyncpg.Pool  # assigned in init_pool()


async def init_pool() -> None:
    global pool
    pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )


async def close_pool() -> None:
    await pool.close()
