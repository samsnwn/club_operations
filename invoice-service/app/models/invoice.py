"""SQLAlchemy models.

Deliberately minimal: `Invoice` holds capture + extraction state, `Attachment`
the stored original file metadata, `SyncWatermark` the per-source catch-up
cursor. Trust levels mirror README §Phase 0.5.
"""

from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SyncWatermark(Base):
    """Per-source catch-up cursor; ingestion polls from this point onward."""

    __tablename__ = "sync_watermarks"

    source: Mapped[str] = mapped_column(String(32), primary_key=True)
    # Free-form per-protocol cursor (RFC 3501 sequence, Drive changes page…).
    cursor: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Invoice(Base):
    """One captured invoice, from ingestion through review to export."""

    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_invoice_content_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Capture provenance
    source: Mapped[str] = mapped_column(String(16))  # 'drive' | 'gmail' | 'fixture'
    content_hash: Mapped[str] = mapped_column(String(64))

    # Extraction suggestions (never authoritative until confirmed)
    supplier_guess: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_number_guess: Mapped[str | None] = mapped_column(String(64), nullable=True)
    invoice_date_guess: Mapped[str | None] = mapped_column(String(32), nullable=True)
    due_date_guess: Mapped[str | None] = mapped_column(String(32), nullable=True)
    net_guess: Mapped[float | None] = mapped_column(Float, nullable=True)
    vat_guess: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_guess: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    category_guess: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_method_guess: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description_guess: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Review state machine: pending_review → confirmed | rejected
    status: Mapped[str] = mapped_column(String(24), default="pending_review")
    # Final reviewed values (corrections allowed before confirm).
    supplier_final: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_number_final: Mapped[str | None] = mapped_column(String(64), nullable=True)
    invoice_date_final: Mapped[str | None] = mapped_column(String(32), nullable=True)
    due_date_final: Mapped[str | None] = mapped_column(String(32), nullable=True)
    net_final: Mapped[float | None] = mapped_column(Float, nullable=True)
    vat_final: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_final: Mapped[float | None] = mapped_column(Float, nullable=True)
    category_final: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_method_final: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description_final: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Text layer (Tesseract OCR output or PDF text) kept for audit/retraining.
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)


def attachment_path(base_dir: str | Path, content_hash: str) -> Path:
    """Deterministic storage path for an original capture file."""
    return Path(base_dir) / content_hash[:2] / content_hash
