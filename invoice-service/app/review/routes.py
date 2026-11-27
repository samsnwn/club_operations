"""Review queue API (PLAN.md §Phase 0.5): list open invoices, inspect one with
its suggestions, confirm/correct/reject. Auth: the backend facade
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
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_db
from app.models.invoice import OPEN_STATUSES, REQUIRED_FIELDS, Invoice

router = APIRouter(tags=["review"])
log = logging.getLogger(__name__)

# `reviewed_by` is String(64) in the model; keep the forwarded identity within it.
MAX_REVIEWER_LENGTH = 64

QUEUE_LIMIT = 200


def internal_token(authorization: Annotated[str | None, Header()] = None) -> None:
    """Require the internal service token (constant-time comparison)."""
    provided = authorization.removeprefix("Bearer ").strip() if authorization else ""
    expected = get_settings().internal_token
    if not (
        provided
        and expected
        and secrets.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
    ):
        raise HTTPException(status_code=401, detail="Invalid internal service token")


def current_reviewer(
    _: Annotated[None, Depends(internal_token)],
    x_reviewer: Annotated[str | None, Header()] = None,
) -> str:
    """The reviewing identity forwarded by the facade. A bare header never
    authenticates; requests without one (system work) are "backend"."""
    reviewer = (x_reviewer or "").strip()
    return reviewer[:MAX_REVIEWER_LENGTH] if reviewer else "backend"


def queue(
    db: Session, status: str = "open", limit: int | None = QUEUE_LIMIT
) -> list[Invoice]:
    """Invoices in `status` ("open" = every open status): needs-attention
    first, then oldest first. `limit=None` returns every match, for callers
    where a full count matters."""
    statuses = OPEN_STATUSES if status == "open" else (status,)
    query = (
        db.query(Invoice)
        .filter(Invoice.status.in_(statuses))
        .order_by(Invoice.status != "needs_attention", Invoice.created_at, Invoice.id)
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def _serialise(invoice: Invoice) -> dict:
    return {
        "id": invoice.id,
        "source": invoice.source,
        "status": invoice.status,
        "created_at": invoice.created_at.isoformat(),
        "suggestions": invoice.suggestions(),
        "missing_fields": invoice.missing_fields(),
    }


@router.get("/queue")
def list_queue(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_reviewer)],
    status: str = "open",
) -> dict:
    rows = queue(db, status)
    return {"count": len(rows), "items": [_serialise(row) for row in rows]}


@router.get("/queue/{invoice_id}")
def get_item(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_reviewer)],
) -> dict:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {**_serialise(invoice), "extracted_text": invoice.extracted_text}


Amount = Annotated[
    Decimal | None, Field(allow_inf_nan=False, max_digits=12, decimal_places=2)
]


class ReviewPayload(BaseModel):
    """Final values: any field may be corrected before confirm. Values land
    in `*_final`; confirmed rows are the only exported rows."""

    model_config = ConfigDict(str_strip_whitespace=True)

    supplier: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    net: Amount = None
    vat: Amount = None
    gross: Amount = None
    category: str | None = None
    payment_method: str | None = None
    description: str | None = None


def _review(db: Session, invoice_id: int, values: dict) -> None:
    """Apply a review decision only while the invoice is still open.

    The status check is part of the UPDATE itself, so two reviewers acting on
    the same invoice cannot both win; the loser gets 409.
    """
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    result = db.execute(
        update(Invoice)
        .where(Invoice.id == invoice_id, Invoice.status.in_(OPEN_STATUSES))
        .values(**values, reviewed_at=dt.datetime.now())
        .execution_options(synchronize_session=False)
    )
    db.commit()
    if result.rowcount:
        return
    db.refresh(invoice)
    if invoice.status == "confirmed" and values["status"] == "rejected":
        raise HTTPException(
            status_code=409,
            detail="Already confirmed — ask the accountant to fix the sheet instead",
        )
    raise HTTPException(status_code=409, detail=f"Already {invoice.status}")


@router.post("/queue/{invoice_id}/confirm")
def confirm(
    invoice_id: int,
    payload: ReviewPayload,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[str, Depends(current_reviewer)],
) -> dict:
    finals = {
        name: value
        for name, value in payload.model_dump().items()
        if value not in (None, "")
    }
    missing = [name for name in REQUIRED_FIELDS if name not in finals]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Required before confirming: {', '.join(missing)}",
        )
    # Reviewer-confirmed data is the source of record for export (hard rule 1).
    _review(
        db,
        invoice_id,
        {
            **{f"{name}_final": value for name, value in finals.items()},
            "status": "confirmed",
            "reviewed_by": reviewer,
        },
    )
    log.info("Invoice %s confirmed by %s", invoice_id, reviewer)
    return {"id": invoice_id, "status": "confirmed", "reviewed_by": reviewer}


@router.post("/queue/{invoice_id}/reject")
def reject(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[str, Depends(current_reviewer)],
) -> dict:
    _review(db, invoice_id, {"status": "rejected", "reviewed_by": reviewer})
    return {"id": invoice_id, "status": "rejected"}
