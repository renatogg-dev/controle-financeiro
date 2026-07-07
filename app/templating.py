"""Shared Jinja2Templates instance used by the web (HTMX) routers."""

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
