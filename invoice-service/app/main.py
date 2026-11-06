"""FastAPI application factory and module entry point — Phase 0.5 service.

Run in development:

    uv run uvicorn app.main:app --reload --port 8081

Versioned REST API under `/api/v1/` (same convention as the main backend) so
Phase 1 can integrate the service instead of replacing it (README §Phase 0.5).
"""

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    api = FastAPI(title=settings.app_name, lifespan=_lifespan)
    api.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    return api


async def _lifespan(api: FastAPI):
    """Scheduled-run scaffolding: the catch-up poll + digest schedule plugs in
    here once the credential wiring lands. Nothing periodic runs today."""
    yield


app = create_app()
