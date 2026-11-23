"""Local drop-folder ingestion for the first real-invoice demonstration.

The folder is written by hand (Finder copies, browser downloads), so captures
must be safe while a file is still being written: a file is only offered to
the pipeline once it looks settled — either observed with an unchanged size
and modification time twice, or untouched for longer than a short settle
window. A copy in progress keeps refreshing its modification time, so neither
rule can fire mid-write.

Hidden files (macOS .DS_Store, editor temp files) and subdirectories are never
captured, and files above the configured attachment limit are skipped without
being read (ingest_file re-checks as the source-agnostic backstop).

Known limitation: a copy that stalls (no writes) for longer than the settle
window or between two polls can still be captured mid-flight, and its
completion would then queue a second row. Ruling that out needs a
producer-side convention (drop via atomic rename) — acceptable for
demonstration use.
"""

import logging
import time
from collections.abc import Callable
from pathlib import Path

from app.ingestion.capture import CapturedFile

log = logging.getLogger(__name__)

# A file untouched for this long counts as settled even on first observation.
# Short enough that an Import click shortly after copying works; long enough
# for a normal copy to have finished writing.
SETTLE_SECONDS = 5.0


class DropFolderSource:
    name = "drop_folder"

    def __init__(
        self,
        directory: str | Path,
        *,
        max_attachment_bytes: int,
        settle_seconds: float = SETTLE_SECONDS,
    ) -> None:
        self.directory = Path(directory)
        self.max_attachment_bytes = max_attachment_bytes
        self.settle_seconds = settle_seconds
        # Previous observation (size, mtime_ns) per candidate path: a file
        # whose observation is unchanged between two polls is settled.
        self._observed: dict[Path, tuple[int, int]] = {}

    def poll(self, is_known: Callable[[str], bool] | None = None) -> list[CapturedFile]:
        """Every settled file currently in the folder. Files stay in place,
        so later polls offer them again; the pipeline dedupes by content
        (`is_known` is accepted for symmetry with the invoice folder)."""
        files: list[CapturedFile] = []
        if not self.directory.is_dir():
            # The folder was removed or recreated: observations can no longer
            # refer to files in it.
            self._observed.clear()
            return files
        now = time.time()
        for path in sorted(self.directory.iterdir()):
            if path.name.startswith("."):
                continue  # .DS_Store and other dotfiles are never invoices
            if not path.is_file():
                continue
            try:
                stat = path.stat()
            except OSError:
                log.warning("Drop-folder file vanished during stat: %s", path.name)
                continue
            if stat.st_size > self.max_attachment_bytes:
                log.warning(
                    "Drop-folder file rejected: %s is %d bytes (limit %d)",
                    path.name,
                    stat.st_size,
                    self.max_attachment_bytes,
                )
                continue
            fingerprint = (stat.st_size, stat.st_mtime_ns)
            unchanged_since_last_poll = self._observed.get(path) == fingerprint
            self._observed[path] = fingerprint
            untouched_long_enough = now - stat.st_mtime >= self.settle_seconds
            if not (unchanged_since_last_poll or untouched_long_enough):
                continue
            try:
                content = path.read_bytes()
            except OSError:
                log.warning("Drop-folder file vanished before read: %s", path.name)
                continue
            files.append(
                CapturedFile(source=self.name, filename=path.name, content=content)
            )
        return files
