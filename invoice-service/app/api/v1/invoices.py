"""Internal invoice-service endpoints used by the main backend facade."""

import threading
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_db
from app.ingestion import pipeline
from app.ingestion.drive import DriveAccessRefused, DriveUnavailable
from app.models.invoice import Invoice, attachment_path
from app.review.routes import internal_token

router = APIRouter(prefix="/internal/invoices", tags=["internal"])

# One import at a time: a run can take minutes (OCR), and a second concurrent
# run would OCR every file twice. Process-local by design (the service runs as
# a single process); `ingest_file` treats a unique-constraint collision as a
# duplicate, which is the backstop if that ever changes.
_import_lock = threading.Lock()


@router.post("/import")
def import_invoices(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(internal_token)],
) -> dict:
    """Import from the invoice folder (or the local inbox in development).
    A broken Drive connection fails visibly instead of reporting 0 new."""
    if not _import_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="An import is already running")
    try:
        return {"new_invoices": pipeline.import_invoices(db)}
    except DriveUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DriveAccessRefused as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        _import_lock.release()


@router.get("/{invoice_id}/original")
def original_file(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(internal_token)],
) -> FileResponse:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    path = attachment_path(get_settings().attachments_dir, invoice.content_hash)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Original file not found")
    media_type = "application/octet-stream"
    with path.open("rb") as file:
        header = file.read(12)
    if header.startswith(b"%PDF"):
        media_type = "application/pdf"
    elif header.startswith(b"\x89PNG"):
        media_type = "image/png"
    elif header.startswith(b"\xff\xd8\xff"):
        media_type = "image/jpeg"
    elif header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        media_type = "image/webp"
    return FileResponse(path, media_type=media_type)
