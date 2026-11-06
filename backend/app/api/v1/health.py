"""Health-check endpoints used by monitoring and deployment checks."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import get_db

router = APIRouter(tags=["health"])


def check_health(db: Session) -> dict:
    """Liveness plus a round-trip database check, shared by all health routes."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@router.get("/health")
def health(db: Annotated[Session, Depends(get_db)]) -> dict:
    """Versioned health endpoint under `/api/v1/`."""
    return check_health(db)
