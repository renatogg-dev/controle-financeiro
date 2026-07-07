"""Full-page HTML routes: landing redirect and auth pages."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from starlette.responses import Response

from app.deps import CurrentUser, DbSession
from app.security import clear_session_cookie, set_session_cookie
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)
from app.templating import templates

router = APIRouter()


@router.get("/")
def index(user: CurrentUser) -> RedirectResponse:
    return RedirectResponse(url="/app" if user else "/login", status_code=303)


@router.get("/login")
def login_page(request: Request, user: CurrentUser) -> Response:
    if user:
        return RedirectResponse(url="/app", status_code=303)
    return templates.TemplateResponse(request, "auth/login.html", {})


@router.post("/login")
def login_submit(
    request: Request, db: DbSession, email: str = Form(...), password: str = Form(...)
) -> Response:
    try:
        user = authenticate_user(db, email, password)
    except InvalidCredentialsError:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"error": "Email ou senha incorretos.", "email": email},
            status_code=401,
        )

    response = RedirectResponse(url="/app", status_code=303)
    set_session_cookie(response, user.id)
    return response


@router.get("/register")
def register_page(request: Request, user: CurrentUser) -> Response:
    if user:
        return RedirectResponse(url="/app", status_code=303)
    return templates.TemplateResponse(request, "auth/register.html", {})


@router.post("/register")
def register_submit(
    request: Request, db: DbSession, email: str = Form(...), password: str = Form(...)
) -> Response:
    if len(password) < 8:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"error": "A senha deve ter pelo menos 8 caracteres.", "email": email},
            status_code=422,
        )

    try:
        user = register_user(db, email, password)
    except EmailAlreadyRegisteredError:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"error": "Este email já está cadastrado.", "email": email},
            status_code=409,
        )

    response = RedirectResponse(url="/app", status_code=303)
    set_session_cookie(response, user.id)
    return response


@router.post("/logout")
def logout_submit() -> Response:
    response = RedirectResponse(url="/login", status_code=303)
    clear_session_cookie(response)
    return response
