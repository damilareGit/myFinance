"""Password hashing and JWT issuance/verification.

JWTs are delivered in an httponly cookie rather than returned as a bearer
token — the frontend never touches the token directly, which keeps the
client code (and the security surface) simple for a non-technical user
base.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
_IS_PRODUCTION = ENVIRONMENT == "production"

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
if _IS_PRODUCTION and JWT_SECRET == "dev-secret-change-me":
    raise RuntimeError(
        "JWT_SECRET must be set to a real secret when ENVIRONMENT=production "
        "— anyone could forge login sessions with the default value."
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 14  # 14 days

COOKIE_NAME = "finadvisor_session"

# Frontend and backend are deployed to different subdomains (e.g.
# finadvisor.onrender.com vs finadvisor-api.onrender.com), which browsers
# treat as different *sites* even though both are HTTPS — SameSite=Lax
# cookies never get attached to those cross-site requests. SameSite=None
# is required for that setup and itself requires Secure (HTTPS), which
# both dev and prod satisfy differently — Lax+non-secure locally over
# http://localhost, None+secure once deployed.
COOKIE_SAMESITE = "none" if _IS_PRODUCTION else "lax"
COOKIE_SECURE = _IS_PRODUCTION

# Called directly rather than through passlib's CryptContext: passlib 1.7.4's
# bcrypt backend-detection probe is incompatible with bcrypt>=4.1 and raises
# on every hash() call. bcrypt truncates at 72 bytes internally, so cap
# input to avoid silently-different hashes for very long passwords.
_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    truncated = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(truncated, hashed.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    sub = payload.get("sub")
    return int(sub) if sub is not None else None
