"""FastAPI application factory and module entry point.

Run in development:

    uv run uvicorn app.main:app --reload --port 8000
"""

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.api.v1.health import check_health
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.db.base import get_db


def create_app() -> FastAPI:
    settings = get_settings()
    api = FastAPI(title=settings.app_name)
    api.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    # Unversioned alias at the root: local tooling probes /health directly.
    # Hidden from the OpenAPI docs; /api/v1/health remains the canonical route.
    @api.get("/health", include_in_schema=False)
    def root_health(db: Session = Depends(get_db)) -> dict:
        return check_health(db)

    return api


app = create_app()
