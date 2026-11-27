"""FastAPI application factory and module entry point — Phase 0.5 service.

Run in development:

    INVOICE_ENVIRONMENT=development uv run uvicorn app.main:app --reload --port 8081

Versioned REST API under `/api/v1/` (same convention as the main backend) so
Phase 1 can integrate the service instead of replacing it (PLAN.md §Phase 0.5).
"""

import logging

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import DEFAULT_INTERNAL_TOKEN, Settings, get_settings

log = logging.getLogger(__name__)


def _validate_security(settings: Settings) -> None:
    """Refuse to start with known development credentials outside development.

    The internal token grants full access to invoice data and bypasses the
    backend facade, so an unconfigured deployment must fail loudly rather than
    inherit the public default. The development stack opts in explicitly with
    `INVOICE_ENVIRONMENT=development`.
    """
    if not settings.internal_token:
        raise RuntimeError(
            "Refusing to start: INVOICE_INTERNAL_TOKEN must not be empty"
        )
    if settings.environment != "development":
        if settings.internal_token == DEFAULT_INTERNAL_TOKEN:
            raise RuntimeError(
                "Refusing to start with the development internal token outside "
                "development. Set INVOICE_INTERNAL_TOKEN to a unique secret, or "
                "set INVOICE_ENVIRONMENT=development for local use."
            )
    else:
        if settings.internal_token == DEFAULT_INTERNAL_TOKEN:
            log.warning(
                "Using the development internal token; never expose this "
                "service outside local development."
            )


def create_app() -> FastAPI:
    settings = get_settings()
    _validate_security(settings)
    api = FastAPI(title=settings.app_name, lifespan=_lifespan)
    api.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    return api


async def _lifespan(api: FastAPI):
    """Scheduled-run scaffolding: the catch-up poll + digest schedule plugs in
    here once the credential wiring lands. Nothing periodic runs today."""
    yield


app = create_app()
