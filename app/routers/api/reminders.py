"""JSON API: bill reminders CRUD + mark paid."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import DbSession, require_login_api
from app.models import Reminder, User
from app.schemas import ReminderCreate, ReminderRead
from app.services import reminder_service as svc

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


def _to_read(reminder: Reminder) -> ReminderRead:
    return ReminderRead(
        id=reminder.id,
        name=reminder.name,
        amount=reminder.amount,
        due_date=reminder.due_date,
        notes=reminder.notes,
        is_paid=reminder.is_paid,
        status=svc.get_status(reminder).value,
    )


@router.get("", response_model=list[ReminderRead])
def list_reminders(
    db: DbSession,
    user: User = Depends(require_login_api),  # noqa: B008
) -> list[ReminderRead]:
    return [_to_read(r) for r in svc.list_reminders(db, user.id)]


@router.post("", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    db: DbSession,
    user: User = Depends(require_login_api),  # noqa: B008
) -> ReminderRead:
    reminder = svc.create_reminder(db, user.id, **payload.model_dump())
    return _to_read(reminder)


@router.patch("/{reminder_id}/paid", response_model=ReminderRead)
def mark_paid(
    reminder_id: int,
    is_paid: bool,
    db: DbSession,
    user: User = Depends(require_login_api),  # noqa: B008
) -> ReminderRead:
    reminder = svc.set_paid(db, user.id, reminder_id, is_paid)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return _to_read(reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int,
    db: DbSession,
    user: User = Depends(require_login_api),  # noqa: B008
) -> None:
    if not svc.delete_reminder(db, user.id, reminder_id):
        raise HTTPException(status_code=404, detail="Reminder not found")
