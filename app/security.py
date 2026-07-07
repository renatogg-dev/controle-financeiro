"""Password hashing, session-cookie JWTs, and CSRF token helpers."""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Response

from app.config import get_settings

settings = get_settings()

SESSION_COOKIE_NAME = "session"
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_session_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(days=settings.session_max_age_days),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(user_id),
        max_age=settings.session_max_age_days * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def csrf_token_for(session_jti: str) -> str:
    """Derive a CSRF token deterministically from the session's jti.

    No separate CSRF cookie is needed: the token is an HMAC of a value
    already sealed inside the signed session JWT, so a page render and a
    later form POST always agree without extra server-side state.
    """
    return hmac.new(
        settings.secret_key.encode("utf-8"), session_jti.encode("utf-8"), hashlib.sha256
    ).hexdigest()
