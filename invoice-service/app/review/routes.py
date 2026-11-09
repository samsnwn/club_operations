"""Review queue API (README §Phase 0.5): list pending items, inspect one with
the extracted suggestions, confirm/correct/reject. Auth: the backend facade
authenticates the user and forwards the username in `X-Reviewer`; that header
is only trusted together with the internal service token. There is no second
credential path — direct use requires the internal token, and reviewer identity
is whatever the trusted caller forwards.

Only CONFIRMED invoices are eligible for export — the human review point is
the gate between extraction and the accounting sheet (hard rules 1 and 3).
"""

import datetime as dt
import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_db
from app.models.invoice import Invoice

router = APIRouter(tags=["review"])
log = logging.getLogger(__name__)

FINAL_FIELDS = (
    "supplier",
    "invoice_number",
    "invoice_date",
    "due_date",
    "net",
    "vat",
    "gross",
    "category",
    "payment_method",
    "description",
)

# `reviewed_by` is String(64) in the model; keep the forwarded identity within it.
MAX_REVIEWER_LENGTH = 64


def _token_matches(provided: str, expected: str) -> bool:
    """Constant-time comparison that also tolerates non-ASCII header input."""
    if not provided or not expected:
        return False
    return secrets.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def internal_token(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().internal_token
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not _token_matches(token, expected):
        raise HTTPException(status_code=401, detail="Invalid internal service token")


def current_reviewer(
    authorization: Annotated[str | None, Header()] = None,
    x_reviewer: Annotated[str | None, Header()] = None,
) -> str:
    """Resolve the reviewing identity.

    The backend facade holds the internal token and forwards the authenticated
    username as `X-Reviewer`; a bare header never authenticates. Requests
    without the header (scheduled/system work) are attributed to "backend".
    """
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not _token_matches(token, get_settings().internal_token):
        raise HTTPException(status_code=401, detail="Unrecognised reviewer token")
    reviewer = (x_reviewer or "").strip()
    return reviewer[:MAX_REVIEWER_LENGTH] if reviewer else "backend"


def _serialise(invoice: Invoice) -> dict:
    guesses = {
        column.name[: -len("_guess")]: getattr(invoice, column.name)
        for column in Invoice.__table__.columns
        if column.name.endswith("_guess") and getattr(invoice, column.name) is not None
    }
    return {
        "id": invoice.id,
        "source": invoice.source,
        "status": invoice.status,
        "confidence": invoice.confidence,
        "created_at": invoice.created_at.isoformat(),
        "suggestions": guesses,
        "supplier_guess": invoice.supplier_guess,
    }


@router.get("/queue")
def list_queue(
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[str, Depends(current_reviewer)],
    status: str = "pending_review",
) -> dict:
    """Pending items, confident captures first (stage 1: all need closing)."""
    rows = (
        db.query(Invoice)
        .filter(Invoice.status == status)
        .order_by(Invoice.confidence.desc(), Invoice.created_at.asc())
        .limit(200)
        .all()
    )
    return {"count": len(rows), "items": [_serialise(row) for row in rows]}


@router.get("/queue/{invoice_id}")
def get_item(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[str, Depends(current_reviewer)],
) -> dict:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    payload = _serialise(invoice)
    payload["extracted_text"] = invoice.extracted_text
    return payload


class ReviewPayload(BaseModel):
    """Correction payload: any field may be overridden before confirm.
    Values land in `*_final`; confirmed rows are the only exported rows."""

    supplier: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    net: float | None = None
    vat: float | None = None
    gross: float | None = None
    category: str | None = None
    payment_method: str | None = None
    description: str | None = None


@router.post("/queue/{invoice_id}/confirm")
def confirm(
    invoice_id: int,
    payload: ReviewPayload,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[str, Depends(current_reviewer)],
) -> dict:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "confirmed":
        raise HTTPException(status_code=409, detail="Already confirmed")
    for fieldname in FINAL_FIELDS:
        value = getattr(payload, fieldname, None)
        if value is not None:
            setattr(invoice, f"{fieldname}_final", value)
    # Reviewer-confirmed data is sourced-of-record for export (hard rule 1).
    invoice.status = "confirmed"
    invoice.reviewed_by = reviewer
    invoice.reviewed_at = dt.datetime.now()
    db.commit()
    log.info("Invoice %s confirmed by %s", invoice.id, reviewer)
    return {"id": invoice.id, "status": invoice.status, "reviewed_by": reviewer}


@router.post("/queue/{invoice_id}/reject")
def reject(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[str, Depends(current_reviewer)],
) -> dict:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "confirmed":
        raise HTTPException(
            status_code=409,
            detail="Already confirmed — ask the accountant to fix the sheet instead",
        )
    invoice.status = "rejected"
    invoice.reviewed_by = reviewer
    invoice.reviewed_at = dt.datetime.now()
    db.commit()
    return {"id": invoice.id, "status": invoice.status}
