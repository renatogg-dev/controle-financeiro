"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.deps import NotAuthenticatedError
from app.routers.api import auth as api_auth
from app.routers.api import reminders as api_reminders
from app.routers.api import transactions as api_transactions
from app.routers.web import pages as web_pages
from app.routers.web import reminders as web_reminders
from app.routers.web import transactions as web_transactions

settings = get_settings()

app = FastAPI(
    title="Controle Financeiro API",
    description="Personal finance tracker: transactions, monthly goals and bill reminders.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(api_auth.router)
app.include_router(api_transactions.router)
app.include_router(api_reminders.router)
app.include_router(web_pages.router)
app.include_router(web_transactions.router)
app.include_router(web_reminders.router)


@app.exception_handler(NotAuthenticatedError)
def handle_not_authenticated(request: Request, exc: NotAuthenticatedError) -> Response:
    if request.headers.get("HX-Request") == "true":
        return Response(status_code=200, headers={"HX-Redirect": "/login"})
    return Response(status_code=303, headers={"Location": "/login"})


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
