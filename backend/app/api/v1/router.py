"""Complete list of everything served under `/api/v1/`."""

from fastapi import APIRouter

from app.api.v1 import health, invoices
from app.auth import routes as auth
from app.auth import user_routes

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(user_routes.router)
# Invoice routes declare `current_user` themselves so they can forward the
# reviewer identity; a signed-in user is still required for every one of them.
api_v1_router.include_router(invoices.router)
