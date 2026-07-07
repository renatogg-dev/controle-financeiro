"""Shared FastAPI dependencies: current user, login gates, CSRF check."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import SESSION_COOKIE_NAME, csrf_token_for, decode_session_token

DbSession = Annotated[Session, Depends(get_db)]


class NotAuthenticatedError(Exception):
    """Raised by web-facing routes when there's no valid session.

    Handled by an exception handler in app.main so it can redirect a normal
    page load to /login, or send an HX-Redirect for HTMX requests.
    """


def get_current_user(request: Request, db: DbSession) -> User | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    payload = decode_session_token(token)
    if payload is None:
        return None

    return db.get(User, int(payload["sub"]))


CurrentUser = Annotated[User | None, Depends(get_current_user)]


def require_login_web(user: CurrentUser) -> User:
    if user is None:
        raise NotAuthenticatedError()
    return user


def require_login_api(user: CurrentUser) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_csrf_token(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    payload = decode_session_token(token)
    if payload is None:
        return None

    return csrf_token_for(payload["jti"])


def verify_csrf(request: Request) -> None:
    """Guard for state-changing HTMX (browser cookie + form) routes.

    JSON `api/*` routes are intentionally not gated by this: they require
    `Content-Type: application/json`, which a cross-site form submission
    cannot forge, so the content-type check itself is the CSRF mitigation
    there and keeps the interactive /docs "Try it out" flow usable without
    a manually-supplied header.
    """
    expected = get_csrf_token(request)
    provided = request.headers.get("X-CSRF-Token")
    if expected is None or provided != expected:
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")
