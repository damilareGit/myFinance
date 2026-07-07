from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_session
from .models import User
from .security import COOKIE_NAME, decode_access_token


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Not authenticated.")
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(401, "Session expired or invalid.")
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(401, "User no longer exists.")
    return user


async def get_current_user_id(user: User = Depends(get_current_user)) -> int:
    """Convenience dependency for routes that only need the id."""
    return user.id
