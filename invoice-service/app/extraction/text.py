"""Text-layer extraction from captured files.

PDFs with a text layer go through pypdf directly. Photo/scan OCR via
Tesseract corresponds to Python 50% of the volume (owner answer #3) — the
OCR node is kept behind `ocr_text()` so it can be swapped for a local vision
model later without touching the pipeline. Tesseract is NOT a Python dep:
the Docker image installs the system package; host dev tests run on PDF
fixtures only until then.
"""

import io
import subprocess

from pypdf import PdfReader


def pdf_text(content: bytes) -> str:
    """Extract the embedded text layer (empty string when scanned-only)."""
    try:
        reader = PdfReader(io.BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:  # noqa: BLE001 — corrupt files must not break ingest
        return ""


def has_text_layer(content: bytes) -> bool:
    return bool(pdf_text(content).strip())


def ocr_text(content: bytes) -> str:
    """Tesseract OCR for image inputs. Clean skip when the binary is missing
    (dev/TestSimple until the Docker image ships it)."""
    try:
        result = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", "deu+eng"],
            input=content,
            capture_output=True,
            check=False,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace")
