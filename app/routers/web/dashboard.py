"""HTMX routes: dashboard page and its month-filtered content fragment."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from app.deps import DbSession, get_csrf_token, require_login_web
from app.json_utils import dumps
from app.models import User
from app.services import transaction_service as svc
from app.templating import templates

router = APIRouter(prefix="/app", dependencies=[Depends(require_login_web)])


def _content_context(db: DbSession, user: User, month: str) -> dict:
    category_breakdown = svc.get_category_breakdown(db, user.id, month)
    monthly_series = svc.get_income_vs_expense_series(db, user.id, month)
    return {
        "month": month,
        "totals": svc.get_monthly_totals(db, user.id, month),
        "category_breakdown": category_breakdown,
        "category_breakdown_json": dumps(category_breakdown),
        "monthly_series_json": dumps(monthly_series),
    }


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
        active_nav="dashboard",
        csrf_token=get_csrf_token(request),
    )
    return templates.TemplateResponse(request, "dashboard/index.html", context)


@router.get("/content")
def content_fragment(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    month: str | None = None,
) -> Response:
    month = month or date.today().strftime("%Y-%m")
    return templates.TemplateResponse(
        request, "dashboard/_content.html", _content_context(db, user, month)
    )
