"""JSON API: dashboard summary feeding the Chart.js widgets."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import DbSession, require_login_api
from app.models import User
from app.schemas import DashboardSummary
from app.services import transaction_service as svc

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(
    month: str, db: DbSession, user: User = Depends(require_login_api)  # noqa: B008
) -> dict:
    return {
        "month": month,
        "totals": svc.get_monthly_totals(db, user.id, month),
        "category_breakdown": svc.get_category_breakdown(db, user.id, month),
        "monthly_series": svc.get_income_vs_expense_series(db, user.id, month),
    }
