"""Registration and login business logic."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import DEFAULT_CATEGORIES
from app.models import Category, User
from app.security import hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def register_user(db: Session, email: str, password: str) -> User:
    if get_user_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError(email)

    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.flush()  # assign user.id before creating dependent rows

    for name, color in DEFAULT_CATEGORIES:
        db.add(Category(user_id=user.id, name=name, color=color, is_default=True))

    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError(email)
    return user
