"""Unit tests for goal progress calculation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import TransactionType, User
from app.services import goal_service as svc
from app.services import transaction_service as tx_svc
from app.services.auth_service import register_user


@pytest.fixture
def user(db_session: Session) -> User:
    return register_user(db_session, "goals@example.com", "password123")


def test_progress_with_no_goal_set(db_session: Session, user: User) -> None:
    progress = svc.get_progress(db_session, user.id, "2026-01")

    assert progress["target"] == Decimal(0)
    assert progress["percent"] == Decimal(0)


def test_progress_capped_at_100_percent(db_session: Session, user: User) -> None:
    category = tx_svc.list_categories(db_session, user.id)[0]
    tx_svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.income,
        amount=Decimal("1000.00"),
        date=date(2026, 1, 10),
        category_id=category.id,
        description="",
    )
    svc.set_goal(db_session, user.id, "2026-01", Decimal("200.00"))

    progress = svc.get_progress(db_session, user.id, "2026-01")

    assert progress["percent"] == Decimal(1)


def test_negative_balance_treated_as_zero_progress(db_session: Session, user: User) -> None:
    category = tx_svc.list_categories(db_session, user.id)[0]
    tx_svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.expense,
        amount=Decimal("500.00"),
        date=date(2026, 1, 10),
        category_id=category.id,
        description="",
    )
    svc.set_goal(db_session, user.id, "2026-01", Decimal("100.00"))

    progress = svc.get_progress(db_session, user.id, "2026-01")

    assert progress["current"] == Decimal(0)
    assert progress["percent"] == Decimal(0)


def test_set_goal_upserts_same_month(db_session: Session, user: User) -> None:
    svc.set_goal(db_session, user.id, "2026-01", Decimal("100.00"))
    svc.set_goal(db_session, user.id, "2026-01", Decimal("300.00"))

    goal = svc.get_goal(db_session, user.id, "2026-01")

    assert goal is not None
    assert goal.target_amount == Decimal("300.00")


def test_shift_month_handles_year_boundary() -> None:
    assert tx_svc.shift_month("2026-01", -1) == "2025-12"
    assert tx_svc.shift_month("2025-12", 1) == "2026-01"
