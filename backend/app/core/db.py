"""Async engine and session factory.

Reads `DATABASE_URL` from the environment, e.g.:
    postgresql+asyncpg://user:password@localhost:5432/finadvisor

Defaults to SQLite for local dev — zero setup, swappable to Postgres
later with no code changes.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models_base import Base


def _normalize_database_url(url: str) -> str:
    """Postgres hosts (Neon, Render, Supabase, ...) hand out a `postgres://`
    or `postgresql://` connection string in the sync psycopg format, often
    with `?sslmode=require` — that query param is psycopg-specific and
    asyncpg raises `TypeError: unexpected keyword argument 'sslmode'` if it
    reaches the driver. Point the scheme at asyncpg and strip the query
    string; SSL is instead passed as a connect arg (see `_connect_args`),
    since every managed Postgres host requires it regardless of what's in
    the URL."""
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    if url.startswith("postgresql+asyncpg://"):
        parts = urlsplit(url)
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    return url


DATABASE_URL = _normalize_database_url(
    os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./finadvisor_dev.db")
)

_connect_args = {"ssl": True} if DATABASE_URL.startswith("postgresql+asyncpg://") else {}

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=_connect_args)
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
