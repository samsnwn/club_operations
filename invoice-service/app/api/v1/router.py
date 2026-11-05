"""Complete list of everything served under `/api/v1/`."""

from fastapi import APIRouter

from app.api.v1 import health
from app.review import routes as review

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(review.router)
