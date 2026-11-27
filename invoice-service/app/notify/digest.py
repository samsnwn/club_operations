"""Digest notifications (owner answer #8): an email with instructions on what
needs attention. Collapsed by design (interim on-demand hosting): one digest covers
every open invoice, so a machine that was off for days
produces a single email, not a backlog of them.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.invoice import Invoice
from app.review.routes import queue

log = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 30
SMTPS_PORT = 465

INSTRUCTIONS = (
    "Anweisungen / instructions: open the review queue, compare each item "
    "against the attached original, correct any field that the machine got "
    "wrong, then press Confirm. Rejected items are kept on file but never "
    "exported. Rechnungen mit fehlenden Pflichtfeldern zuerst pruefen."
)


def build_digest(db: Session) -> str:
    """Human-readable summary of every open invoice, in queue order."""
    items = queue(db, limit=None)
    attention = [item for item in items if item.status == "needs_attention"]
    ready = [item for item in items if item.status == "pending_review"]
    lines = [f"Blue Velvet Invoice Service — {len(items)} item(s) need review", ""]
    if attention:
        lines.append("!! Missing required fields — enter them by hand:")
        lines.extend(
            f"  - #{item.id} {_supplier(item)} — missing "
            f"{', '.join(item.missing_fields())}"
            for item in attention
        )
        lines.append("")
    lines.append("Ready to check and confirm:")
    lines.extend(f"  - #{item.id} {_supplier(item)}" for item in ready)
    lines.append("")
    lines.append(INSTRUCTIONS)
    return "\n".join(lines)


def _supplier(invoice: Invoice) -> str:
    return invoice.supplier_suggested or "(unknown supplier)"


def send_digest(db: Session) -> bool:
    """Send via SMTP when configured; degraded (log-only) mode otherwise so
    runs on a machine without mail credentials still succeed.

    The digest names suppliers, so it only ever travels over verified TLS:
    implicit TLS on port 465, STARTTLS on any other port. A server that offers
    neither, or presents an untrusted certificate, fails the send — there is
    no plaintext fallback."""
    settings = get_settings()
    body = build_digest(db)
    if not (settings.smtp_host and settings.digest_from and settings.digest_to):
        log.info("SMTP not configured — digest not sent. Content:\n%s", body)
        return False
    message = EmailMessage()
    message["From"] = settings.digest_from
    message["To"] = settings.digest_to
    # Subject collapses the state: one mail replaces the missed dailies.
    message["Subject"] = "[Blue Velvet] Invoice review digest"
    message.set_content(body)
    context = ssl.create_default_context()
    try:
        if settings.smtp_port == SMTPS_PORT:
            connection = smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=SMTP_TIMEOUT_SECONDS,
                context=context,
            )
        else:
            connection = smtplib.SMTP(
                settings.smtp_host, settings.smtp_port, timeout=SMTP_TIMEOUT_SECONDS
            )
        with connection as smtp:
            if settings.smtp_port != SMTPS_PORT:
                smtp.starttls(context=context)
            if settings.smtp_user and settings.smtp_password:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        log.exception("Digest send failed")
        return False
    return True
