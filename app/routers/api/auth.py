"""JSON API: registration, login, logout, current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.deps import DbSession, require_login_api
from app.models import User
from app.schemas import UserLogin, UserRead, UserRegister
from app.security import clear_session_cookie, set_session_cookie
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, response: Response, db: DbSession) -> User:
    try:
        user = register_user(db, payload.email, payload.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=409, detail="Email already registered") from exc

    set_session_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserRead)
def login(payload: UserLogin, response: Response, db: DbSession) -> User:
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password") from exc

    set_session_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    clear_session_cookie(response)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(require_login_api)) -> User:  # noqa: B008
    return user
