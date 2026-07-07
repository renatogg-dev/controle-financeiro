"""JSON API: per-month savings goal, progress, and history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import DbSession, require_login_api
from app.models import User
from app.schemas import GoalProgress, GoalSet
from app.services import goal_service as svc
from app.services.transaction_service import shift_month

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("/history", response_model=list[GoalProgress])
def history(
    db: DbSession,
    user: User = Depends(require_login_api),  # noqa: B008
    end_month: str = Query(...),
    months: int = Query(default=6, ge=1, le=24),
) -> list[dict]:
    month_keys = [shift_month(end_month, -i) for i in range(months - 1, -1, -1)]
    return svc.get_history(db, user.id, month_keys)


@router.get("/{month}", response_model=GoalProgress)
def get_goal_progress(
    month: str, db: DbSession, user: User = Depends(require_login_api)  # noqa: B008
) -> dict:
    return {"month": month, **svc.get_progress(db, user.id, month)}


@router.put("/{month}", response_model=GoalProgress)
def set_goal(
    month: str,
    payload: GoalSet,
    db: DbSession,
    user: User = Depends(require_login_api),  # noqa: B008
) -> dict:
    svc.set_goal(db, user.id, month, payload.target_amount)
    return {"month": month, **svc.get_progress(db, user.id, month)}
