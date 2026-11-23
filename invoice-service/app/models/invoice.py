"""SQLAlchemy model and the review rules every module shares.

`Invoice` holds one capture from ingestion through review to export.
Vocabulary follows `GLOSSARY.md` (capture, suggestion, required fields, open).
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import DateTime, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Fields extraction can suggest. The reviewer may also fill category, payment
# method and description, which extraction never suggests.
SUGGESTED_FIELDS = (
    "supplier",
    "invoice_number",
    "invoice_date",
    "due_date",
    "net",
    "vat",
    "gross",
)

# A confirmed invoice is export-eligible, so it must at least say who was paid,
# when and how much. The invoice number stays optional (till receipts).
REQUIRED_FIELDS = ("supplier", "invoice_date", "gross")

# Statuses still waiting for a review decision; review moves out of them once.
OPEN_STATUSES = ("needs_attention", "pending_review")

Money = Numeric(12, 2)


class Invoice(Base):
    """One captured invoice, from ingestion through review to export."""

    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_invoice_content_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Capture provenance
    source: Mapped[str] = mapped_column(String(16))  # 'drive' | 'drop_folder'
    content_hash: Mapped[str] = mapped_column(String(64))
    # Drive reports MD5 checksums, so new invoice-folder files are recognised
    # by MD5 before downloading them.
    content_md5: Mapped[str | None] = mapped_column(String(32), index=True)
    # Where the original lives in its channel (the Drive file ID), if anywhere.
    source_ref: Mapped[str | None] = mapped_column(String(128))

    # Suggestions from extraction (never authoritative until confirmed)
    supplier_suggested: Mapped[str | None] = mapped_column(String(255))
    invoice_number_suggested: Mapped[str | None] = mapped_column(String(64))
    invoice_date_suggested: Mapped[str | None] = mapped_column(String(32))
    due_date_suggested: Mapped[str | None] = mapped_column(String(32))
    net_suggested: Mapped[Decimal | None] = mapped_column(Money)
    vat_suggested: Mapped[Decimal | None] = mapped_column(Money)
    gross_suggested: Mapped[Decimal | None] = mapped_column(Money)

    # needs_attention | pending_review → confirmed | rejected
    status: Mapped[str] = mapped_column(String(24), default="pending_review")
    # Final reviewed values (corrections allowed before confirm).
    supplier_final: Mapped[str | None] = mapped_column(String(255))
    invoice_number_final: Mapped[str | None] = mapped_column(String(64))
    invoice_date_final: Mapped[str | None] = mapped_column(String(32))
    due_date_final: Mapped[str | None] = mapped_column(String(32))
    net_final: Mapped[Decimal | None] = mapped_column(Money)
    vat_final: Mapped[Decimal | None] = mapped_column(Money)
    gross_final: Mapped[Decimal | None] = mapped_column(Money)
    category_final: Mapped[str | None] = mapped_column(String(64))
    payment_method_final: Mapped[str | None] = mapped_column(String(64))
    description_final: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[str | None] = mapped_column(String(64))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Text layer (Tesseract OCR output or PDF text) kept for audit/retraining.
    extracted_text: Mapped[str | None] = mapped_column(Text)

    def suggestions(self) -> dict:
        return {
            name: value
            for name in SUGGESTED_FIELDS
            if (value := getattr(self, f"{name}_suggested")) is not None
        }

    def missing_fields(self) -> list[str]:
        """Required fields extraction did not suggest."""
        suggested = self.suggestions()
        return [name for name in REQUIRED_FIELDS if name not in suggested]


def attachment_path(base_dir: str | Path, content_hash: str) -> Path:
    """Deterministic storage path for an original capture file."""
    return Path(base_dir) / content_hash[:2] / content_hash
