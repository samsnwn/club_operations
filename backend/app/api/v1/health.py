"""Health-check endpoints used by monitoring and deployment checks."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.base import get_db

router = APIRouter(tags=["health"])

log = logging.getLogger(__name__)


def check_health(db: Session) -> dict | JSONResponse:
    """Liveness plus a round-trip database check, shared by all health routes.

    A database failure answers 503 `degraded`; the details stay in the log.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        log.exception("Health check database round-trip failed")
        return JSONResponse(
            status_code=503, content={"status": "degraded", "database": "error"}
        )
    return {"status": "ok", "database": "ok"}


@router.get("/health", response_model=None)
def health(db: Annotated[Session, Depends(get_db)]) -> dict | JSONResponse:
    """Versioned health endpoint under `/api/v1/`."""
    return check_health(db)
