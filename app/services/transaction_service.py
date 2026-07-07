"""Transaction CRUD, filtering/pagination, and category listing."""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Category, Transaction, TransactionType


def get_month_key(d: date) -> str:
    return d.strftime("%Y-%m")


def month_bounds(month_key: str) -> tuple[date, date]:
    """Return [start, end) date bounds for a "YYYY-MM" key.

    Used instead of a DB-side strftime() filter so month filtering works
    identically on SQLite and Postgres.
    """
    year, month = (int(part) for part in month_key.split("-"))
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def list_categories(db: Session, user_id: int) -> list[Category]:
    return list(
        db.scalars(select(Category).where(Category.user_id == user_id).order_by(Category.name))
    )


def get_category(db: Session, user_id: int, category_id: int) -> Category | None:
    return db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )


def create_transaction(
    db: Session,
    user_id: int,
    *,
    type: TransactionType,
    amount: Decimal,
    date: date,
    category_id: int,
    description: str,
) -> Transaction | None:
    if get_category(db, user_id, category_id) is None:
        return None

    transaction = Transaction(
        user_id=user_id,
        type=type,
        amount=amount,
        date=date,
        category_id=category_id,
        description=description.strip(),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_transaction(db: Session, user_id: int, transaction_id: int) -> Transaction | None:
    return db.scalar(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    )


def update_transaction(
    db: Session,
    user_id: int,
    transaction_id: int,
    *,
    type: TransactionType,
    amount: Decimal,
    date: date,
    category_id: int,
    description: str,
) -> Transaction | None:
    transaction = get_transaction(db, user_id, transaction_id)
    if transaction is None or get_category(db, user_id, category_id) is None:
        return None

    transaction.type = type
    transaction.amount = amount
    transaction.date = date
    transaction.category_id = category_id
    transaction.description = description.strip()
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, user_id: int, transaction_id: int) -> bool:
    transaction = get_transaction(db, user_id, transaction_id)
    if transaction is None:
        return False
    db.delete(transaction)
    db.commit()
    return True


def list_transactions(
    db: Session,
    user_id: int,
    *,
    month: str | None = None,
    category_id: int | None = None,
    type: TransactionType | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Transaction], int]:
    stmt = (
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.user_id == user_id)
    )
    if month:
        start, end = month_bounds(month)
        stmt = stmt.where(Transaction.date >= start, Transaction.date < end)
    if category_id:
        stmt = stmt.where(Transaction.category_id == category_id)
    if type:
        stmt = stmt.where(Transaction.type == type)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(stmt))
    return items, total


def export_transactions_csv(db: Session, user_id: int) -> str:
    items, _ = list_transactions(db, user_id, page=1, page_size=1_000_000)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "type", "category", "amount", "description"])
    for t in items:
        writer.writerow(
            [t.date.isoformat(), t.type.value, t.category.name, t.amount, t.description]
        )
    return buffer.getvalue()
