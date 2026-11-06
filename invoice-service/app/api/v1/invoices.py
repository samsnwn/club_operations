"""Internal invoice-service endpoints used by the main backend facade."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_db
from app.ingestion.pipeline import poll_drop_folder
from app.models.invoice import Invoice, attachment_path
from app.review.routes import internal_token

router = APIRouter(prefix="/internal/invoices", tags=["internal"])


@router.post("/import")
def import_drop_folder(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(internal_token)],
) -> dict:
    return {"new_invoices": poll_drop_folder(db)}


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
