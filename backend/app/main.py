"""FastAPI application factory and module entry point.

Run in development:

    uv run uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    api = FastAPI(title=settings.app_name)
    api.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    return api


app = create_app()
