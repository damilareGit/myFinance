"""Async engine and session factory.

Reads `DATABASE_URL` from the environment, e.g.:
    postgresql+asyncpg://user:password@localhost:5432/finadvisor

Defaults to SQLite for local dev — zero setup, swappable to Postgres
later with no code changes.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models_base import Base

def _normalize_database_url(url: str) -> str:
    """Render (and most Postgres hosts) hand out a `postgres://` or
    `postgresql://` connection string with no driver specified — that's the
    sync psycopg format. Point it at asyncpg instead so it works with our
    async engine, without requiring the host's dashboard to know about it."""
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _normalize_database_url(
    os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./finadvisor_dev.db")
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_models() -> None:
    """Create tables if they don't exist. Call once at app startup.

    For production, prefer Alembic migrations over this — it's here for
    local dev/testing.
    """
    # Import every module that defines a model so it registers on
    # Base.metadata before create_all runs.
    from ..auth import models as _auth_models  # noqa: F401
    from ..categories import models as _category_models  # noqa: F401
    from ..goals import models as _goal_models  # noqa: F401
    from ..transactions import models as _transaction_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def session_scope():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncSession:
    """FastAPI dependency: `session: AsyncSession = Depends(get_session)`."""
    async with SessionLocal() as session:
        yield session
