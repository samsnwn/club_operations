"""Complete list of everything served under `/api/v1/`."""

from fastapi import APIRouter

from app.api.v1 import health, invoices

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(invoices.router)
