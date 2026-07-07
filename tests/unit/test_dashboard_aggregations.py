"""Unit tests for dashboard aggregation helpers in transaction_service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import TransactionType, User
from app.services import transaction_service as svc
from app.services.auth_service import register_user


@pytest.fixture
def user(db_session: Session) -> User:
    return register_user(db_session, "dash@example.com", "password123")


def test_category_breakdown_excludes_zero_expense_categories(
    db_session: Session, user: User
) -> None:
    categories = svc.list_categories(db_session, user.id)
    food, transport = categories[0], categories[1]
    svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.expense,
        amount=Decimal("50.00"),
        date=date(2026, 1, 5),
        category_id=food.id,
        description="",
    )

    breakdown = svc.get_category_breakdown(db_session, user.id, "2026-01")

    names = {item["category"] for item in breakdown}
    assert names == {food.name}
    assert transport.name not in names


def test_category_breakdown_ignores_income(db_session: Session, user: User) -> None:
    category = svc.list_categories(db_session, user.id)[0]
    svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.income,
        amount=Decimal("1000.00"),
        date=date(2026, 1, 5),
        category_id=category.id,
        description="",
    )

    breakdown = svc.get_category_breakdown(db_session, user.id, "2026-01")

    assert breakdown == []


def test_income_vs_expense_series_spans_year_boundary(db_session: Session, user: User) -> None:
    category = svc.list_categories(db_session, user.id)[0]
    svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.income,
        amount=Decimal("100.00"),
        date=date(2025, 10, 15),
        category_id=category.id,
        description="",
    )

    series = svc.get_income_vs_expense_series(db_session, user.id, "2026-02", months=6)

    months = [item["month"] for item in series]
    assert months == ["2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02"]
    october = next(item for item in series if item["month"] == "2025-10")
    assert october["income"] == Decimal("100.00")


def test_income_vs_expense_series_default_window_is_six_months(
    db_session: Session, user: User
) -> None:
    series = svc.get_income_vs_expense_series(db_session, user.id, "2026-06")

    assert len(series) == 6
    assert series[-1]["month"] == "2026-06"
