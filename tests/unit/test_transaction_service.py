"""Unit tests for transaction service business logic (no HTTP layer)."""

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
    return register_user(db_session, "unit@example.com", "password123")


@pytest.mark.parametrize(
    ("month_key", "expected_start", "expected_end"),
    [
        ("2026-03", date(2026, 3, 1), date(2026, 4, 1)),
        ("2026-12", date(2026, 12, 1), date(2027, 1, 1)),
    ],
)
def test_month_bounds(month_key: str, expected_start: date, expected_end: date) -> None:
    start, end = svc.month_bounds(month_key)
    assert (start, end) == (expected_start, expected_end)


def test_create_transaction_rejects_category_from_another_user(
    db_session: Session, user: User
) -> None:
    other = register_user(db_session, "other@example.com", "password123")
    other_category = svc.list_categories(db_session, other.id)[0]

    result = svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.expense,
        amount=Decimal("10.00"),
        date=date(2026, 1, 1),
        category_id=other_category.id,
        description="",
    )

    assert result is None


def test_list_transactions_filters_by_month(db_session: Session, user: User) -> None:
    category = svc.list_categories(db_session, user.id)[0]
    svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.expense,
        amount=Decimal("10.00"),
        date=date(2026, 1, 15),
        category_id=category.id,
        description="January",
    )
    svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.expense,
        amount=Decimal("20.00"),
        date=date(2026, 2, 15),
        category_id=category.id,
        description="February",
    )

    items, total = svc.list_transactions(db_session, user.id, month="2026-01")

    assert total == 1
    assert items[0].description == "January"


def test_list_transactions_pagination(db_session: Session, user: User) -> None:
    category = svc.list_categories(db_session, user.id)[0]
    for day in range(1, 6):
        svc.create_transaction(
            db_session,
            user.id,
            type=TransactionType.expense,
            amount=Decimal("1.00"),
            date=date(2026, 1, day),
            category_id=category.id,
            description=f"tx-{day}",
        )

    page1, total = svc.list_transactions(db_session, user.id, page=1, page_size=2)
    page2, _ = svc.list_transactions(db_session, user.id, page=2, page_size=2)

    assert total == 5
    assert len(page1) == 2
    assert len(page2) == 2
    assert {t.id for t in page1}.isdisjoint({t.id for t in page2})


def test_update_transaction_returns_none_for_other_users_transaction(
    db_session: Session, user: User
) -> None:
    other = register_user(db_session, "other2@example.com", "password123")
    category = svc.list_categories(db_session, user.id)[0]
    transaction = svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.expense,
        amount=Decimal("10.00"),
        date=date(2026, 1, 1),
        category_id=category.id,
        description="mine",
    )
    assert transaction is not None

    result = svc.update_transaction(
        db_session,
        other.id,
        transaction.id,
        type=TransactionType.expense,
        amount=Decimal("99.00"),
        date=date(2026, 1, 1),
        category_id=category.id,
        description="hijacked",
    )

    assert result is None


def test_delete_transaction_returns_false_for_other_users_transaction(
    db_session: Session, user: User
) -> None:
    other = register_user(db_session, "other3@example.com", "password123")
    category = svc.list_categories(db_session, user.id)[0]
    transaction = svc.create_transaction(
        db_session,
        user.id,
        type=TransactionType.expense,
        amount=Decimal("10.00"),
        date=date(2026, 1, 1),
        category_id=category.id,
        description="mine",
    )
    assert transaction is not None

    assert svc.delete_transaction(db_session, other.id, transaction.id) is False
