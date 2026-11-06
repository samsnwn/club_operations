"""The ingest pipeline: hash de-duplication, storage, extraction to
suggestions, and first-pass trust assessment. Everything produces review-queue
rows — never exports, never sheet writes (hard rules 1 and 2).
"""

import hashlib
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.extraction import fields as field_parser
from app.extraction import text as text_extractor
from app.ingestion.base import CapturedFile
from app.models.invoice import Invoice, SyncWatermark, attachment_path

log = logging.getLogger(__name__)

# Stage 1 rollout threshold (README §Phase 0.5): humans confirm everything;
# confident captures simply sort first in the review queue.
AUTO_OK_THRESHOLD = 0.8


def _status_for(consumed_fields: int, confidence: float) -> str:
    """Stage-1 rollout: humans confirm everything. Low-confidence captures
    carry a distinct status so the review UI can surface them first."""
    if consumed_fields == 0 or confidence < 0.5:
        return "needs_attention"
    return "pending_review"


def _document_text(content: bytes, max_pdf_pages: int) -> str:
    """Text layer routing: PDF → embedded text; anything decodable as plain
    UTF-8 text → itself; otherwise → OCR (photos/scans, ~50% per owner answer
    #3). Empty/failed OCR simply yields no suggestions."""
    if content.startswith(b"%PDF"):
        text = text_extractor.pdf_text(content, max_pages=max_pdf_pages)
        return text if text.strip() else text_extractor.ocr_text(content)
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        return text_extractor.ocr_text(content)
    printable = sum(ch.isprintable() or ch in "\n\r\t" for ch in decoded) / max(
        len(decoded), 1
    )
    return decoded if printable >= 0.9 else text_extractor.ocr_text(content)


def poll_sources(db: Session, sources: list) -> int:
    """Run every configured source once: catch-up poll → dedupe → store →
    extract → queue rows. Returns the number of NEW invoices captured.
    Source failures are isolated per source: one broken channel never blocks
    the others."""
    new_count = 0
    for source in sources:
        cursor_row = db.get(SyncWatermark, source.name)
        cursor = cursor_row.cursor if cursor_row else None
        try:
            captured, next_cursor = source.poll(cursor)
        except Exception:
            log.exception("Source %s poll failed", source.name)
            continue
        for captured_file in captured:
            if ingest_file(db, captured_file):
                new_count += 1
        watermark = cursor_row or SyncWatermark(source=source.name)
        watermark.cursor = next_cursor
        watermark.last_success_at = datetime.now(UTC).replace(tzinfo=None)
        db.add(watermark)
    db.commit()
    return new_count


def poll_fixture_source(db: Session) -> int:
    """Run the deterministic fixture source for the development workflow."""
    from app.ingestion.fixtures import FixtureSource

    return poll_sources(db, [FixtureSource()])


def poll_drop_folder(db: Session) -> int:
    """Import new files from the configured local demonstration inbox."""
    from app.ingestion.drop_folder import DropFolderSource

    settings = get_settings()
    return poll_sources(db, [DropFolderSource(settings.inbox_dir)])


def ingest_file(db: Session, captured: CapturedFile) -> bool:
    """Store + extract one captured file. Returns False for duplicates
    (same content hash channels never create review rows twice)."""
    settings = get_settings()
    content_size = len(captured.content)
    if content_size > settings.max_attachment_bytes:
        log.warning(
            "Capture rejected: %s from %s is %d bytes (limit %d)",
            captured.filename,
            captured.source,
            content_size,
            settings.max_attachment_bytes,
        )
        return False

    if captured.content.startswith(b"%PDF"):
        page_count = text_extractor.pdf_page_count(captured.content)
        if page_count is not None and page_count > settings.max_pdf_pages:
            log.warning(
                "Capture rejected: %s from %s has %d PDF pages (limit %d)",
                captured.filename,
                captured.source,
                page_count,
                settings.max_pdf_pages,
            )
            return False

    content_hash = hashlib.sha256(captured.content).hexdigest()
    if db.query(Invoice.id).filter(Invoice.content_hash == content_hash).first():
        log.info(
            "Duplicate capture skipped: %s (%s)", captured.filename, content_hash[:12]
        )
        return False

    storage_path = attachment_path(settings.attachments_dir, content_hash)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(captured.content)

    text = _document_text(captured.content, settings.max_pdf_pages)
    if len(text) > settings.max_extracted_text_chars:
        log.warning(
            "Extracted text truncated: %s from %d to %d characters",
            captured.filename,
            len(text),
            settings.max_extracted_text_chars,
        )
        text = text[: settings.max_extracted_text_chars]

    extraction = field_parser.extract_fields(text)

    invoice = Invoice(
        source=captured.source,
        content_hash=content_hash,
        extracted_text=text or None,
        supplier_guess=extraction.supplier,
        confidence=round(extraction.confidence, 2),
        status=_status_for(len(extraction.fields), extraction.confidence),
    )
    for fieldname, value in extraction.fields.items():
        if fieldname in _GUARDED_FIELDS and isinstance(value, (int, float, str)):
            setattr(invoice, f"{fieldname}_guess", value)
    db.add(invoice)
    db.commit()
    log.info(
        "Ingested %s from %s (confidence %.2f, status %s)",
        captured.filename,
        captured.source,
        extraction.confidence,
        invoice.status,
    )
    return True


_GUARDED_FIELDS: frozenset[str] = frozenset(
    {
        "invoice_number",
        "invoice_date",
        "due_date",
        "net",
        "vat",
        "gross",
        "category",
        "payment_method",
        "description",
    }
)
