"""Health-check endpoints used by monitoring and deployment checks."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Liveness plus a round-trip database check."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
