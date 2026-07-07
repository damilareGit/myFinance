"""FinAdvisor backend entry point.

Run locally with:
    uvicorn backend.app.main:app --reload
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.routes import router as auth_router
from .categories.routes import router as categories_router
from .categories.seed import seed_global_defaults
from .core.db import get_session, init_models
from .goals.routes import router as goals_router
from .transactions.routes import router as transactions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    async for session in get_session():
        await seed_global_defaults(session)
        break
    yield


app = FastAPI(title="FinAdvisor", lifespan=lifespan)

# The frontend runs on a different port in dev (different origin, same
# "site"), so the httponly session cookie needs explicit CORS + credentials
# support — a wildcard origin can't be combined with allow_credentials.
_frontend_origins = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(categories_router, prefix="/categories", tags=["categories"])
app.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
app.include_router(goals_router, prefix="/goals", tags=["goals"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
