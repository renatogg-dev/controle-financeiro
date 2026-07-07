"""Reminder CRUD and due-date status logic."""

from __future__ import annotations

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Reminder


class ReminderStatus(enum.StrEnum):
    paid = "paid"
    overdue = "overdue"
    due_soon = "due_soon"
    ok = "ok"


DUE_SOON_WINDOW_DAYS = 7


def get_status(reminder: Reminder, today: date | None = None) -> ReminderStatus:
    if reminder.is_paid:
        return ReminderStatus.paid

    today = today or date.today()
    days_until_due = (reminder.due_date - today).days

    if days_until_due < 0:
        return ReminderStatus.overdue
    if days_until_due <= DUE_SOON_WINDOW_DAYS:
        return ReminderStatus.due_soon
    return ReminderStatus.ok


def list_reminders(db: Session, user_id: int) -> list[Reminder]:
    return list(
        db.scalars(select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.due_date))
    )


def get_reminder(db: Session, user_id: int, reminder_id: int) -> Reminder | None:
    return db.scalar(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user_id)
    )


def create_reminder(
    db: Session,
    user_id: int,
    *,
    name: str,
    amount: Decimal | None,
    due_date: date,
    notes: str | None,
) -> Reminder:
    reminder = Reminder(
        user_id=user_id,
        name=name.strip(),
        amount=amount,
        due_date=due_date,
        notes=(notes or "").strip() or None,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def set_paid(db: Session, user_id: int, reminder_id: int, is_paid: bool) -> Reminder | None:
    reminder = get_reminder(db, user_id, reminder_id)
    if reminder is None:
        return None
    reminder.is_paid = is_paid
    db.commit()
    db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, user_id: int, reminder_id: int) -> bool:
    reminder = get_reminder(db, user_id, reminder_id)
    if reminder is None:
        return False
    db.delete(reminder)
    db.commit()
    return True
