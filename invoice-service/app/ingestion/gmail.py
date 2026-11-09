"""Gmail ingestion (secondary, automated channel) via the dedicated
forwarding mailbox.

NOT YET WIRED: Gmail API credentials live outside the repo (hard rule 4).
When configured, this polls the forwarding mailbox with `since`-watermark
semantics, extracts attachments, and labels processed messages (never
deletes). Until then it degrades to a clean not-configured skip.
"""

import logging

from app.ingestion.base import CapturedFile

log = logging.getLogger(__name__)


class GmailSource:
    name = "gmail"

    def __init__(
        self, mailbox: str | None = None, credentials_path: str | None = None
    ) -> None:
        self._configured = bool(mailbox and credentials_path)

    def poll(self, cursor: str | None) -> tuple[list[CapturedFile], str]:
        if not self._configured:
            log.info(
                "Gmail source not configured — skipping (plan: dedicated forwarding mailbox, OAuth outside the repo)."
            )
            return [], cursor or ""
        raise NotImplementedError(
            "Gmail API wiring lands when owner credentials exist (Phase 0.5 step)."
        )
