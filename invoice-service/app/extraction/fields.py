"""Field extraction: always a *suggestion* with an explicit confidence
score (README §Phase 0.5). Text-layer based for now (PDF text and Tesseract
output); supplier-specific templates arrive per-supplier as real data lands.

Document contents are untrusted input (hard rule 6): defensive regexes only,
nothing here acts beyond recording suggestions in the review queue.
"""

import re
from dataclasses import dataclass, field
from typing import Final

# Common German/English club-invoice patterns (bounded, defensive).
_PATTERNS: Final = (
    (
        r"Rechnung(?:s-)?(?:nummer|Nr\.?)[:\s]*([A-Za-z0-9/\-]{2,24})",
        "invoice_number",
        0.8,
    ),
    (r"Invoice(?: number| no\.?)[:\s]*([A-Za-z0-9/\-]{2,24})", "invoice_number", 0.8),
    (r"Rechnungsdatum[:\s]*([0-3]?\d\.\s?\d{1,2}\.\s?\d{2,4})", "invoice_date", 0.7),
    (r"Rechnungsdatum[:\s]*(\d{4}-\d{2}-\d{2})", "invoice_date", 0.7),
    (
        r"F[aä]llig(?:keitsdatum)?[:\s]*([0-3]?\d\.\s?\d{1,2}\.\s?\d{2,4})",
        "due_date",
        0.7,
    ),
    (
        r"Due(?: date)?[:\s]*([0-3]?\d\.\s?\d{1,2}\.\s?\d{2,4}|\d{4}-\d{2}-\d{2})",
        "due_date",
        0.7,
    ),
    (r"Betrag[:\s]*€?\s*(\d{1,4}(?:[.]\d{3})*,\d{2})", "gross", 0.6),
    (r"Gesamt(?:betrag)?[:\s]*€?\s*(\d{1,4}(?:[.]\d{3})*,\d{2})", "gross", 0.6),
    (r"Total(?: amount)?[:\s]*€?\s*(\d{1,4}(?:[.]\d{3})*,\d{2})", "gross", 0.6),
    (r"Netto(?:betrag)?[:\s]*€?\s*(\d{1,4}(?:[.]\d{3})*,\d{2})", "net", 0.6),
    (r"MwSt(?:\s*\d+%,?)?[:\s]*€?\s*(\d{1,4}(?:[.]\d{3})*,\d{2})", "vat", 0.5),
    (r"(?:Ausweisung der )?USt[:\s]*€?\s*(\d{1,4}(?:[.]\d{3})*,\d{2})", "vat", 0.5),
)


@dataclass
class Suggestion:
    """One extracted field: value plus confidence, pending human review."""

    field: str
    value: str | float | None
    confidence: float


@dataclass
class Extraction:
    supplier: str | None = None
    fields: dict[str, float | str] = field(default_factory=dict)
    confidences: dict[str, float] = field(default_factory=dict)

    def add(self, suggestion: Suggestion) -> None:
        self.fields[suggestion.field] = suggestion.value
        self.confidences[suggestion.field] = suggestion.confidence

    @property
    def confidence(self) -> float:
        """Average per-field confidence, 0.0 when nothing was recognised."""
        if not self.confidences:
            return 0.0
        return sum(self.confidences.values()) / len(self.confidences)


def _parse_amount(raw: str) -> float | None:
    """German decimal format `1.234,56` → float; non-matching → None."""
    if not re.fullmatch(r"\d{1,4}(?:[.]\d{3})*,\d{2}", raw):
        return None
    return float(raw.replace(".", "").replace(",", "."))


def parse_supplier(text: str) -> str | None:
    """Naive: first plausible header line (kept honest for manual review)."""
    lines = [line.strip() for line in (text or "").splitlines()]
    for line in lines[:8]:
        if 2 <= len(line) <= 64 and not line.startswith(("Rechnung", "Invoice")):
            return line
    return None


def extract_fields(text: str) -> Extraction:
    """Regex pass over a document text layer. Never raises on malformed
    input: unrecognised documents simply yield a low-confidence, empty
    suggestion set that lands in the review queue for manual entry."""
    extraction = Extraction(supplier=parse_supplier(text))
    for pattern, fieldname, confidence in _PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match is None:
            continue
        if fieldname in ("gross", "net", "vat"):
            value = _parse_amount(match.group(1))
        else:
            value = match.group(1).strip()
        if value is not None:
            extraction.add(
                Suggestion(field=fieldname, value=value, confidence=confidence)
            )
    return extraction
