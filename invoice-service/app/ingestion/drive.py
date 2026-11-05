"""Drive-folder ingestion (primary channel).

NOT YET WIRED: requires Drive API credentials outside the repo (hard rule 3).
When credentials exist, this polls one configured folder via changes from the
sync watermark and captures new files. Until then, `poll` degrades to a clean
not-configured skip so pipeline runs still succeed.
"""

import logging

from app.ingestion.base import CapturedFile

log = logging.getLogger(__name__)


class DriveSource:
    name = "drive"

    def __init__(
        self, folder_id: str | None = None, credentials_path: str | None = None
    ) -> None:
        self._configured = bool(folder_id and credentials_path)

    def poll(self, cursor: str | None) -> tuple[list[CapturedFile], str]:
        if not self._configured:
            log.info(
                "Drive source not configured — skipping (plan: OAuth credentials outside the repo)."
            )
            return [], cursor or ""
        raise NotImplementedError(
            "Drive API wiring lands when owner credentials exist (Phase 0.5 step)."
        )
