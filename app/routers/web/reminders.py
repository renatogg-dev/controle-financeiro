"""HTMX routes: reminders page, list fragment, create/pay/delete mutations."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from starlette.responses import Response

from app.deps import DbSession, get_csrf_token, require_login_web, verify_csrf
from app.htmx_utils import toast_header
from app.models import User
from app.services import reminder_service as svc
from app.templating import templates

router = APIRouter(prefix="/app/reminders", dependencies=[Depends(require_login_web)])


def _list_context(db: DbSession, user: User) -> dict:
    reminders = svc.list_reminders(db, user.id)
    return {
        "reminders": [(r, svc.get_status(r)) for r in reminders],
    }


@router.get("")
def index(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
) -> Response:
    context = _list_context(db, user)
    context.update(
        current_user=user,
        active_nav="reminders",
        csrf_token=get_csrf_token(request),
    )
    return templates.TemplateResponse(request, "reminders/index.html", context)


@router.get("/list")
def list_fragment(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
) -> Response:
    return templates.TemplateResponse(request, "reminders/_list.html", _list_context(db, user))


@router.post("", dependencies=[Depends(verify_csrf)])
def create(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    name: str = Form(...),
    amount: Decimal | None = Form(default=None),
    due_date: date = Form(...),
    notes: str = Form(""),
) -> Response:
    svc.create_reminder(db, user.id, name=name, amount=amount, due_date=due_date, notes=notes)
    response = templates.TemplateResponse(request, "reminders/_list.html", _list_context(db, user))
    response.headers.update(toast_header("Lembrete adicionado."))
    return response


@router.patch("/{reminder_id}/paid", dependencies=[Depends(verify_csrf)])
def toggle_paid(
    request: Request,
    reminder_id: int,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    is_paid: bool = Form(...),
) -> Response:
    reminder = svc.set_paid(db, user.id, reminder_id, is_paid)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Lembrete não encontrado")
    return templates.TemplateResponse(request, "reminders/_list.html", _list_context(db, user))


@router.delete("/{reminder_id}", dependencies=[Depends(verify_csrf)])
def delete(
    request: Request,
    reminder_id: int,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
) -> Response:
    if not svc.delete_reminder(db, user.id, reminder_id):
        raise HTTPException(status_code=404, detail="Lembrete não encontrado")
    response = templates.TemplateResponse(request, "reminders/_list.html", _list_context(db, user))
    response.headers.update(toast_header("Lembrete excluído."))
    return response
