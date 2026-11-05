"""Review queue API (README §Phase 0.5): list pending items, inspect one with
the extracted suggestions, confirm/correct/reject. Auth: simple per-user
bearer tokens (owner + one admin — owner answer #5).

Only CONFIRMED invoices are eligible for export — the human review point is
the gate between extraction and the accounting sheet (hard rule 1).
"""

import datetime as dt
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.base import get_db
from app.models.invoice import Invoice
from sqlalchemy.orm import Session

router = APIRouter(tags=["review"])
log = logging.getLogger(__name__)

FINAL_FIELDS = ("supplier", "invoice_number", "invoice_date", "due_date", "net", "vat", "gross", "category",
                "payment_method", "description")


def current_reviewer(authorization: Annotated[str | None, Header()] = None) -> str:
    expected = get_settings().review_tokens
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    for username, expected_token in expected.items():
        if token and token == expected_token:
            return username
    raise HTTPException(status_code=401, detail="Unrecognised reviewer token")


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
def list_queue(status: str = "pending_review", db: Session = Depends(get_db),
               reviewer: str = Depends(current_reviewer)) -> dict:
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
def get_item(invoice_id: int, db: Session = Depends(get_db), reviewer: str = Depends(current_reviewer)) -> dict:
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
def confirm(invoice_id: int, payload: ReviewPayload, db: Session = Depends(get_db),
            reviewer: str = Depends(current_reviewer)) -> dict:
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
def reject(invoice_id: int, db: Session = Depends(get_db), reviewer: str = Depends(current_reviewer)) -> dict:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "confirmed":
        raise HTTPException(status_code=409, detail="Already confirmed — ask the accountant to fix the sheet instead")
    invoice.status = "rejected"
    invoice.reviewed_by = reviewer
    invoice.reviewed_at = dt.datetime.now()
    db.commit()
    return {"id": invoice.id, "status": invoice.status}
