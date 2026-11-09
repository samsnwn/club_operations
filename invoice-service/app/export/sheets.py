"""Google Sheets export — **feature-flagged OFF** (owner answer #4: the
column mapping is confirmed against the real sheet before the first write).

The design is fixed already, so wiring later is mechanical:
- append-only via the Sheets API: `values.append` on the configured tab;
- one row per CONFIRMED invoice (with `*_final` values, never guesses);
- columns: export date, source file link, supplier, invoice number, dates,
  net, VAT, gross, category, payment method, description, hash;
- corrected/re-exported invoices append a new row with a supersede note —
  the sheet is never edited in place and formula columns are never touched
  (hard rules 1 and 3).
"""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.invoice import Invoice

COLUMNS_HINT = (
    "export_date | source | supplier | invoice_number | invoice_date | "
    "due_date | net | vat | gross | category | payment_method | description | content_hash"
)


def export_confirmed(db: Session) -> int:
    """Append confirmed-but-not-yet-exported invoices to the accounting
    sheet. Global no-op while `INVOICE_EXPORT_ENABLED` is false."""
    if not get_settings().export_enabled:
        return 0
    raise NotImplementedError(
        "Sheets API wiring lands only after the column mapping is confirmed "
        f"against the real sheet. Planned row shape: {COLUMNS_HINT}"
    )


def pending_export_count(db: Session) -> int:
    return (
        db.query(Invoice)
        .filter(Invoice.status == "confirmed", Invoice.exported_at.is_(None))
        .count()
    )
