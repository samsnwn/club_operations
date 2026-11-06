"""FastAPI application factory and module entry point.

Run in development:

    uv run uvicorn app.main:app --reload --port 8080
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import get_settings

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _allowed_origins() -> set[str]:
    settings = get_settings()
    return {
        origin.strip().rstrip("/")
        for origin in settings.allowed_origins.split(",")
        if origin.strip()
    }


def create_app() -> FastAPI:
    settings = get_settings()
    api = FastAPI(title=settings.app_name)

    @api.middleware("http")
    async def same_origin_guard(request: Request, call_next):
        """Cookie auth plus SameSite=Lax is the CSRF baseline; additionally
        reject state-changing requests from an origin we do not serve."""
        if request.method in UNSAFE_METHODS:
            origin = request.headers.get("origin")
            if origin:
                allowed = _allowed_origins()
                allowed.add(str(request.base_url).rstrip("/"))
                if origin.rstrip("/") not in allowed:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Cross-origin request rejected"},
                    )
        return await call_next(request)

    api.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    return api


app = create_app()
