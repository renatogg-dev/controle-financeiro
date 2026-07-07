"""Per-month savings goal CRUD, progress calculation, and history."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Goal
from app.services.transaction_service import get_monthly_totals


def get_goal(db: Session, user_id: int, month: str) -> Goal | None:
    return db.scalar(select(Goal).where(Goal.user_id == user_id, Goal.month == month))


def set_goal(db: Session, user_id: int, month: str, target_amount: Decimal) -> Goal:
    goal = get_goal(db, user_id, month)
    if goal is None:
        goal = Goal(user_id=user_id, month=month, target_amount=target_amount)
        db.add(goal)
    else:
        goal.target_amount = target_amount
    db.commit()
    db.refresh(goal)
    return goal


def get_progress(db: Session, user_id: int, month: str) -> dict[str, Decimal]:
    goal = get_goal(db, user_id, month)
    target = goal.target_amount if goal else Decimal(0)
    current = max(get_monthly_totals(db, user_id, month)["balance"], Decimal(0))
    percent = min(current / target, Decimal(1)) if target > 0 else Decimal(0)
    return {"target": target, "current": current, "percent": percent}


def get_history(db: Session, user_id: int, months: list[str]) -> list[dict]:
    """Target vs. actual balance for each of the given "YYYY-MM" keys."""
    history = []
    for month in months:
        progress = get_progress(db, user_id, month)
        history.append({"month": month, **progress})
    return history
