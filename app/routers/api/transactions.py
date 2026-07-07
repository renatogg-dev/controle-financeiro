"""JSON API: transactions CRUD, categories, CSV export."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.deps import DbSession, require_login_api
from app.models import Transaction, TransactionType, User
from app.schemas import CategoryRead, PaginatedTransactions, TransactionCreate, TransactionRead
from app.services import transaction_service as svc

router = APIRouter(prefix="/api", tags=["transactions"])


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: DbSession, user: User = Depends(require_login_api)) -> list:  # noqa: B008
    return svc.list_categories(db, user.id)


@router.get("/transactions", response_model=PaginatedTransactions)
def list_transactions(
    db: DbSession,
    user: User = Depends(require_login_api),  # noqa: B008
    month: str | None = None,
    category_id: int | None = None,
    type: TransactionType | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    items, total = svc.list_transactions(
        db, user.id, month=month, category_id=category_id, type=type, page=page, page_size=page_size
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/transactions/export.csv")
def export_transactions_csv(
    db: DbSession, user: User = Depends(require_login_api)  # noqa: B008
) -> StreamingResponse:
    csv_data = svc.export_transactions_csv(db, user.id)
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transacoes.csv"},
    )


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate, db: DbSession, user: User = Depends(require_login_api)  # noqa: B008
) -> Transaction:
    transaction = svc.create_transaction(db, user.id, **payload.model_dump())
    if transaction is None:
        raise HTTPException(status_code=422, detail="Invalid category")
    return transaction


@router.get("/transactions/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int, db: DbSession, user: User = Depends(require_login_api)  # noqa: B008
) -> Transaction:
    transaction = svc.get_transaction(db, user.id, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    payload: TransactionCreate,
    db: DbSession,
    user: User = Depends(require_login_api),  # noqa: B008
) -> Transaction:
    transaction = svc.update_transaction(db, user.id, transaction_id, **payload.model_dump())
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int, db: DbSession, user: User = Depends(require_login_api)  # noqa: B008
) -> None:
    if not svc.delete_transaction(db, user.id, transaction_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
