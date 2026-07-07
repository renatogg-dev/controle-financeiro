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


def shift_month(month_key: str, delta: int) -> str:
    """Return the "YYYY-MM" key `delta` months away from `month_key`."""
    year, month = (int(part) for part in month_key.split("-"))
    total = year * 12 + (month - 1) + delta
    new_year, new_month = divmod(total, 12)
    return f"{new_year:04d}-{new_month + 1:02d}"


def month_bounds(month_key: str) -> tuple[date, date]:
    """Return [start, end) date bounds for a "YYYY-MM" key.

    Used instead of a DB-side strftime() filter so month filtering works
    identically on SQLite and Postgres.
    """
    year, month = (int(part) for part in month_key.split("-"))
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def get_monthly_totals(db: Session, user_id: int, month: str) -> dict[str, Decimal]:
    start, end = month_bounds(month)
    stmt = select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id, Transaction.date >= start, Transaction.date < end
    )
    totals: dict[TransactionType, Decimal] = {}
    for transaction_type, total in db.execute(stmt.group_by(Transaction.type)):
        totals[transaction_type] = total

    income = totals.get(TransactionType.income, Decimal(0))
    expense = totals.get(TransactionType.expense, Decimal(0))
    return {"income": income, "expense": expense, "balance": income - expense}


def get_category_breakdown(db: Session, user_id: int, month: str) -> list[dict]:
    """Expense total per category for the month, excluding zero-expense categories."""
    start, end = month_bounds(month)
    stmt = (
        select(Category.name, Category.color, func.sum(Transaction.amount))
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.expense,
            Transaction.date >= start,
            Transaction.date < end,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
    )
    return [
        {"category": name, "color": color, "amount": amount}
        for name, color, amount in db.execute(stmt)
    ]


def get_income_vs_expense_series(
    db: Session, user_id: int, end_month: str, months: int = 6
) -> list[dict]:
    """Income/expense totals for the `months` ending at (and including) `end_month`."""
    month_keys = [shift_month(end_month, -i) for i in range(months - 1, -1, -1)]
    return [{"month": m, **get_monthly_totals(db, user_id, m)} for m in month_keys]


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
