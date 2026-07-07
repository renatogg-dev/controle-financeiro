"""Unit tests for reminder due-date status boundaries."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.models import Reminder
from app.services.reminder_service import DUE_SOON_WINDOW_DAYS, ReminderStatus, get_status

TODAY = date(2026, 6, 15)


def _reminder(due_date: date, is_paid: bool = False) -> Reminder:
    return Reminder(
        id=1,
        user_id=1,
        name="Conta",
        amount=Decimal("10.00"),
        due_date=due_date,
        notes=None,
        is_paid=is_paid,
    )


def test_due_today_is_due_soon() -> None:
    assert get_status(_reminder(TODAY), today=TODAY) == ReminderStatus.due_soon


def test_due_in_exactly_window_days_is_due_soon() -> None:
    due = TODAY + timedelta(days=DUE_SOON_WINDOW_DAYS)
    assert get_status(_reminder(due), today=TODAY) == ReminderStatus.due_soon


def test_due_one_day_past_window_is_ok() -> None:
    due = TODAY + timedelta(days=DUE_SOON_WINDOW_DAYS + 1)
    assert get_status(_reminder(due), today=TODAY) == ReminderStatus.ok


def test_due_yesterday_is_overdue() -> None:
    due = TODAY - timedelta(days=1)
    assert get_status(_reminder(due), today=TODAY) == ReminderStatus.overdue


def test_paid_overrides_overdue() -> None:
    due = TODAY - timedelta(days=30)
    assert get_status(_reminder(due, is_paid=True), today=TODAY) == ReminderStatus.paid


def test_paid_overrides_due_soon() -> None:
    assert get_status(_reminder(TODAY, is_paid=True), today=TODAY) == ReminderStatus.paid
