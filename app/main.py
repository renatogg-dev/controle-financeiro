"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Controle Financeiro API",
    description="Personal finance tracker: transactions, monthly goals and bill reminders.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
