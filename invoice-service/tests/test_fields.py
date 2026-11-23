# Field extraction: suggestions must always fit what confirm accepts.

from decimal import Decimal

from app.extraction.fields import extract_fields


def test_largest_amount_that_fits_is_suggested() -> None:
    suggestions = extract_fields("Gesamt: 9999.999.999,99\n")
    assert suggestions["gross"] == Decimal("9999999999.99")


def test_amount_too_long_for_confirm_is_not_suggested() -> None:
    """OCR noise must not pre-fill a value the confirm endpoint rejects."""
    assert "gross" not in extract_fields("Gesamt: 1.234.567.890.123,45\n")
