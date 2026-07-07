from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..categories.seed import seed_personal_nigeria_rules
from ..core.db import get_session
from .deps import get_current_user
from .models import User
from .security import COOKIE_NAME, COOKIE_SAMESITE, COOKIE_SECURE, create_access_token, hash_password, verify_password

router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        max_age=60 * 60 * 24 * 14,
    )


@router.post("/signup", response_model=UserResponse)
async def signup(
    body: SignupRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(400, "An account with this email already exists.")

    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")

    user_count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    is_first_user = user_count == 0

    user = User(email=body.email, hashed_password=hash_password(body.password), display_name=body.display_name)
    session.add(user)
    await session.flush()

    if is_first_user:
        # The app's owner gets the existing Nigeria-tuned keyword rules
        # (tithe, IKEDC, Cowrywise, ...) as their personal rule set, layered
        # on top of the generalized global defaults. Family members who
        # sign up afterward start with the generalized defaults only.
        await seed_personal_nigeria_rules(session, user.id)

    await session.commit()

    _set_session_cookie(response, user.id)
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)


@router.post("/login", response_model=UserResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password.")

    _set_session_cookie(response, user.id)
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, samesite=COOKIE_SAMESITE, secure=COOKIE_SECURE)
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)
