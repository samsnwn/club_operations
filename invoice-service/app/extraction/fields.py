"""Field extraction: turns a document's text layer into suggestions
(PLAN.md §Phase 0.5). Generic regexes for now; supplier-specific templates
arrive per supplier as real data lands.

Document contents are untrusted input (hard rule 7): defensive, bounded
regexes only, and nothing here acts beyond returning suggestions.
"""

import re
from decimal import Decimal
from typing import Final

_DATE = r"[0-3]?\d\.\s?\d{1,2}\.\s?\d{2,4}"
_ISO_DATE = r"\d{4}-\d{2}-\d{2}"
# At most 10 integer digits (`9999.999.999,99`), so a suggestion always fits
# `Numeric(12,2)` and the confirm schema; longer OCR noise suggests nothing.
_AMOUNT = r"€?\s*(\d{1,4}(?:[.]\d{3}){0,2},\d{2})"
_AMOUNT_FIELDS: Final = frozenset({"net", "vat", "gross"})

# Common German/English club-invoice patterns; the first match per field wins.
_PATTERNS: Final = (
    ("invoice_number", r"Rechnung(?:s-)?(?:nummer|Nr\.?)[:\s]*([A-Za-z0-9/\-]{2,24})"),
    ("invoice_number", r"Invoice(?: number| no\.?)[:\s]*([A-Za-z0-9/\-]{2,24})"),
    ("invoice_date", rf"Rechnungsdatum[:\s]*({_DATE}|{_ISO_DATE})"),
    ("due_date", rf"F[aä]llig(?:keitsdatum)?[:\s]*({_DATE})"),
    ("due_date", rf"Due(?: date)?[:\s]*({_DATE}|{_ISO_DATE})"),
    ("gross", rf"Betrag[:\s]*{_AMOUNT}"),
    ("gross", rf"Gesamt(?:betrag)?[:\s]*{_AMOUNT}"),
    ("gross", rf"Total(?: amount)?[:\s]*{_AMOUNT}"),
    ("net", rf"Netto(?:betrag)?[:\s]*{_AMOUNT}"),
    ("vat", rf"MwSt(?:\s*\d+%,?)?[:\s]*{_AMOUNT}"),
    ("vat", rf"(?:Ausweisung der )?USt[:\s]*{_AMOUNT}"),
)


def _parse_amount(raw: str) -> Decimal:
    """German decimal format `1.234,56` → Decimal('1234.56')."""
    return Decimal(raw.replace(".", "").replace(",", "."))


def _supplier(text: str) -> str | None:
    """Naive: first plausible header line (kept honest for manual review)."""
    for line in text.splitlines()[:8]:
        line = line.strip()
        if 2 <= len(line) <= 64 and not line.startswith(("Rechnung", "Invoice")):
            return line
    return None


def extract_fields(text: str) -> dict[str, str | Decimal]:
    """Suggestions found in a document's text. Never raises on malformed
    input: an unrecognised document simply yields fewer suggestions."""
    suggestions: dict[str, str | Decimal] = {}
    if supplier := _supplier(text):
        suggestions["supplier"] = supplier
    for fieldname, pattern in _PATTERNS:
        if fieldname in suggestions:
            continue
        match = re.search(pattern, text, re.IGNORECASE)
        if match is None:
            continue
        raw = match.group(1).strip()
        suggestions[fieldname] = (
            _parse_amount(raw) if fieldname in _AMOUNT_FIELDS else raw
        )
    return suggestions
