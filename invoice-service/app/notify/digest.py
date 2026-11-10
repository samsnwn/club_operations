"""Digest notifications (owner answer #8): an email with instructions on what
needs attention. Collapsed by design (interim plan A): one digest covers
everything since the last reviewed item, so a machine that was off for days
produces a single email, not a backlog of them.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.invoice import Invoice

log = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 30
SMTPS_PORT = 465

INSTRUCTIONS = (
    "Anweisungen / instructions: open the review queue, compare each item "
    "against the attached original, correct any field that the machine got "
    "wrong, then press Confirm. Rejected items are kept on file but never "
    "exported. Rechnungen mit niedriger Konfidenz zuerst pruefen."
)


def build_digest(db: Session) -> str:
    """Human-readable summary of everything waiting for review, plus counts."""
    pending = (
        db.query(Invoice)
        .filter(Invoice.status.in_(["pending_review", "needs_attention"]))
        .order_by(
            Invoice.confidence.asc()
        )  # worst first — that's where attention is needed
        .all()
    )
    attention = [item for item in pending if item.status == "needs_attention"]
    lines = [
        f"Blue Velvet Invoice Service — {len(pending)} item(s) need review",
        "",
    ]
    if attention:
        lines.append("!! Not recognised automatically — enter the values manually:")
        lines.extend(
            f"  - #{item.id} {item.supplier_guess or '(unknown supplier)'}"
            for item in attention
        )
        lines.append("")
    lines.append("Others (check extracted fields, then confirm):")
    lines.extend(
        f"  - #{item.id} {item.supplier_guess or '(unknown supplier)'} — confidence {item.confidence:.0%}"
        for item in pending
        if item.status == "pending_review"
    )
    lines.append("")
    lines.append(INSTRUCTIONS)
    return "\n".join(lines)


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
