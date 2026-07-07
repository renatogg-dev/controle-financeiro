"""HTMX routes: goals page, progress/history fragment, set-goal mutation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from starlette.responses import Response

from app.deps import DbSession, get_csrf_token, require_login_web, verify_csrf
from app.htmx_utils import toast_header
from app.models import User
from app.services import goal_service as svc
from app.services.transaction_service import shift_month
from app.templating import templates

router = APIRouter(prefix="/app/goals", dependencies=[Depends(require_login_web)])

HISTORY_MONTHS = 6


def _content_context(db: DbSession, user: User, month: str) -> dict:
    progress = svc.get_progress(db, user.id, month)
    month_keys = [shift_month(month, -i) for i in range(HISTORY_MONTHS - 1, -1, -1)]
    history = svc.get_history(db, user.id, month_keys)
    return {"month": month, "progress": progress, "history": history}


@router.get("")
def index(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    month: str | None = None,
) -> Response:
    month = month or date.today().strftime("%Y-%m")
    context = _content_context(db, user, month)
    context.update(
        current_user=user,
        active_nav="goals",
        csrf_token=get_csrf_token(request),
    )
    return templates.TemplateResponse(request, "goals/index.html", context)


@router.get("/content")
def content_fragment(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    month: str | None = None,
) -> Response:
    month = month or date.today().strftime("%Y-%m")
    return templates.TemplateResponse(
        request, "goals/_content.html", _content_context(db, user, month)
    )


@router.put("/{month}", dependencies=[Depends(verify_csrf)])
def set_goal(
    request: Request,
    month: str,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    target_amount: Decimal = Form(...),
) -> Response:
    svc.set_goal(db, user.id, month, target_amount)
    response = templates.TemplateResponse(
        request, "goals/_content.html", _content_context(db, user, month)
    )
    response.headers.update(toast_header("Meta salva."))
    return response
