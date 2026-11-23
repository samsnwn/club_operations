"""The ingest pipeline: content-hash de-duplication, storage, extraction to
suggestions, and the open status. Everything produces review-queue rows —
never exports, never sheet writes (hard rules 1 and 3).
"""

import hashlib
import logging
from functools import lru_cache

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.extraction import fields as field_parser
from app.extraction import text as text_extractor
from app.ingestion.capture import CapturedFile
from app.ingestion.drive import DriveSource
from app.ingestion.drop_folder import DropFolderSource
from app.models.invoice import Invoice, attachment_path

log = logging.getLogger(__name__)


def _document_text(content: bytes, max_pdf_pages: int) -> str:
    """PDF → embedded text layer (OCR when it has none); UTF-8 text → itself;
    anything else (photos/scans, ~50% per owner answer #3) → OCR. Empty or
    failed OCR simply yields no suggestions."""
    if content.startswith(b"%PDF"):
        text = text_extractor.pdf_text(content, max_pages=max_pdf_pages)
        return text if text.strip() else text_extractor.ocr_text(content)
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return text_extractor.ocr_text(content)


def import_from(db: Session, source: DriveSource | DropFolderSource) -> int:
    """Poll an ingestion channel once and ingest every capture. Returns the
    number of NEW invoices. One bad capture never blocks the others; because
    both channels offer their files again on every poll, a failed file is
    retried next run (already-ingested files dedupe by content). Channel-level
    failures (Drive unreachable or refusing access) propagate to the caller."""

    def is_known(md5: str) -> bool:
        known = db.query(Invoice.id).filter(Invoice.content_md5 == md5).first()
        return known is not None

    new_count = 0
    for captured in source.poll(is_known):
        try:
            if ingest_file(db, captured):
                new_count += 1
        except Exception:
            db.rollback()
            log.exception(
                "Ingest failed for %s from %s", captured.filename, captured.source
            )
    return new_count


@lru_cache
def drop_folder_source(directory: str, max_attachment_bytes: int) -> DropFolderSource:
    """One source instance per inbox directory and size limit, so settle-state
    observations survive between import calls. The limit is part of the cache
    key: a settings reload must never reuse a source built with a stale limit
    (clearing the settings cache does not clear this one)."""
    return DropFolderSource(directory, max_attachment_bytes=max_attachment_bytes)


def import_invoices(db: Session) -> int:
    """Import from the invoice folder when Drive is configured, otherwise
    from the local inbox (development, tests, offline demos)."""
    settings = get_settings()
    if settings.drive_folder_id and settings.drive_credentials_file:
        source = DriveSource(
            settings.drive_folder_id,
            settings.drive_credentials_file,
            max_attachment_bytes=settings.max_attachment_bytes,
        )
    else:
        source = drop_folder_source(settings.inbox_dir, settings.max_attachment_bytes)
    return import_from(db, source)


def ingest_file(db: Session, captured: CapturedFile) -> bool:
    """Store + extract one capture. Returns False when it is skipped
    (too large, too many pages, or a duplicate by content hash)."""
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

    # De-duplicate first: the drop folder keeps its files, so every later
    # import sees them again and must not re-parse them.
    content_hash = hashlib.sha256(captured.content).hexdigest()
    content_md5 = hashlib.md5(captured.content, usedforsecurity=False).hexdigest()
    existing = db.query(Invoice).filter(Invoice.content_hash == content_hash).first()
    if existing is not None:
        if existing.content_md5 is None:
            # Rows from before MD5 tracking learn it on first re-capture, so
            # the invoice folder skips this file without downloading it again.
            existing.content_md5 = content_md5
            db.commit()
        log.info(
            "Duplicate capture skipped: %s (%s)", captured.filename, content_hash[:12]
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

    invoice = Invoice(
        source=captured.source,
        source_ref=captured.source_ref,
        content_hash=content_hash,
        content_md5=content_md5,
        extracted_text=text or None,
    )
    for fieldname, value in field_parser.extract_fields(text).items():
        setattr(invoice, f"{fieldname}_suggested", value)
    invoice.status = "needs_attention" if invoice.missing_fields() else "pending_review"
    db.add(invoice)
    try:
        db.commit()
    except IntegrityError:
        # Lost a race with a concurrent ingest of the same content.
        db.rollback()
        log.info(
            "Duplicate capture skipped: %s (%s)", captured.filename, content_hash[:12]
        )
        return False
    log.info(
        "Ingested %s from %s (status %s)",
        captured.filename,
        captured.source,
        invoice.status,
    )
    return True
