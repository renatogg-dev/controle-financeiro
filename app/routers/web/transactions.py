"""HTMX routes: transactions page, list/form fragments, mutations."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.responses import Response

from app.deps import DbSession, get_csrf_token, require_login_web, verify_csrf
from app.htmx_utils import toast_header
from app.models import TransactionType, User
from app.services import transaction_service as svc
from app.templating import templates

router = APIRouter(prefix="/app/transactions", dependencies=[Depends(require_login_web)])


def _list_context(
    request: Request,
    user: User,
    db: DbSession,
    month: str | None,
    category_id: int | None,
    type: TransactionType | None,
    page: int,
) -> dict:
    month = month or date.today().strftime("%Y-%m")
    items, total = svc.list_transactions(
        db, user.id, month=month, category_id=category_id, type=type, page=page, page_size=20
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": 20,
        "month": month,
        "category_id": category_id,
        "type": type,
        "categories": svc.list_categories(db, user.id),
    }


@router.get("")
def index(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    month: str | None = None,
    category_id: int | None = None,
    type: TransactionType | None = None,
    page: int = 1,
) -> Response:
    context = _list_context(request, user, db, month, category_id, type, page)
    context.update(
        current_user=user,
        active_nav="transactions",
        csrf_token=get_csrf_token(request),
        editing=None,
        today=date.today().isoformat(),
    )
    return templates.TemplateResponse(request, "transactions/index.html", context)


@router.get("/list")
def list_fragment(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    month: str | None = None,
    category_id: int | None = None,
    type: TransactionType | None = None,
    page: int = 1,
) -> Response:
    context = _list_context(request, user, db, month, category_id, type, page)
    return templates.TemplateResponse(request, "transactions/_list.html", context)


@router.get("/new")
def new_form(
    request: Request, db: DbSession, user: User = Depends(require_login_web)  # noqa: B008
) -> Response:
    return templates.TemplateResponse(
        request,
        "transactions/_form.html",
        {
            "categories": svc.list_categories(db, user.id),
            "editing": None,
            "today": date.today().isoformat(),
        },
    )


@router.get("/{transaction_id}/edit")
def edit_form(
    request: Request,
    transaction_id: int,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
) -> Response:
    transaction = svc.get_transaction(db, user.id, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return templates.TemplateResponse(
        request,
        "transactions/_form.html",
        {"categories": svc.list_categories(db, user.id), "editing": transaction},
    )


def _render_list_and_reset_form(
    request: Request, user: User, db: DbSession, month: str, message: str
) -> HTMLResponse:
    list_context = _list_context(request, user, db, month, None, None, 1)
    list_html = templates.get_template("transactions/_list.html").render(
        request=request, **list_context
    )
    form_html = templates.get_template("transactions/_form.html").render(
        request=request,
        categories=list_context["categories"],
        editing=None,
        today=date.today().isoformat(),
    )
    body = list_html + f'<div id="transaction-form-container" hx-swap-oob="true">{form_html}</div>'
    return HTMLResponse(content=body, headers=toast_header(message))


@router.post("", dependencies=[Depends(verify_csrf)])
def create(
    request: Request,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    type: TransactionType = Form(...),
    amount: Decimal = Form(...),
    transaction_date: date = Form(..., alias="date"),
    category_id: int = Form(...),
    description: str = Form(""),
) -> Response:
    transaction = svc.create_transaction(
        db,
        user.id,
        type=type,
        amount=amount,
        date=transaction_date,
        category_id=category_id,
        description=description,
    )
    if transaction is None:
        return templates.TemplateResponse(
            request,
            "transactions/_form.html",
            {
                "categories": svc.list_categories(db, user.id),
                "editing": None,
                "error": "Categoria inválida.",
                "today": date.today().isoformat(),
            },
        )
    return _render_list_and_reset_form(
        request, user, db, transaction_date.strftime("%Y-%m"), "Transação adicionada."
    )


@router.put("/{transaction_id}", dependencies=[Depends(verify_csrf)])
def update(
    request: Request,
    transaction_id: int,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    type: TransactionType = Form(...),
    amount: Decimal = Form(...),
    transaction_date: date = Form(..., alias="date"),
    category_id: int = Form(...),
    description: str = Form(""),
) -> Response:
    transaction = svc.update_transaction(
        db,
        user.id,
        transaction_id,
        type=type,
        amount=amount,
        date=transaction_date,
        category_id=category_id,
        description=description,
    )
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return _render_list_and_reset_form(
        request, user, db, transaction_date.strftime("%Y-%m"), "Transação atualizada."
    )


@router.delete("/{transaction_id}", dependencies=[Depends(verify_csrf)])
def delete(
    request: Request,
    transaction_id: int,
    db: DbSession,
    user: User = Depends(require_login_web),  # noqa: B008
    month: str | None = None,
) -> Response:
    transaction = svc.get_transaction(db, user.id, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    svc.delete_transaction(db, user.id, transaction_id)
    context = _list_context(request, user, db, month, None, None, 1)
    response = templates.TemplateResponse(request, "transactions/_list.html", context)
    response.headers.update(toast_header("Transação excluída."))
    return response
