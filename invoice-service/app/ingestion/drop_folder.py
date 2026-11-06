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
from dataclasses import dataclass
from pathlib import Path

from app.ingestion.base import CapturedFile

log = logging.getLogger(__name__)

# A file untouched for this long counts as settled even on first observation.
# Short enough that an Import click shortly after copying works; long enough
# for a normal copy to have finished writing.
SETTLE_SECONDS = 5.0


@dataclass(frozen=True)
class DropFolderCapturedFile:
    source: str
    filename: str
    content: bytes


class DropFolderSource:
    name = "drop_folder"

    def __init__(self, directory: str | Path, *, max_attachment_bytes: int) -> None:
        self.directory = Path(directory)
        self.max_attachment_bytes = max_attachment_bytes
        # Previous observation (size, mtime_ns) per candidate path: a file
        # whose observation is unchanged between two polls is settled.
        self._observed: dict[Path, tuple[int, int]] = {}

    def poll(self, cursor: str | None) -> tuple[list[CapturedFile], str]:
        files: list[CapturedFile] = []
        if not self.directory.is_dir():
            # The folder was removed or recreated: observations can no longer
            # refer to files in it.
            self._observed.clear()
            return files, ""
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
            settled = (
                unchanged_since_last_poll or (now - stat.st_mtime) >= SETTLE_SECONDS
            )
            if not settled:
                continue
            try:
                content = path.read_bytes()
            except OSError:
                log.warning("Drop-folder file vanished before read: %s", path.name)
                continue
            files.append(
                DropFolderCapturedFile(
                    source=self.name,
                    filename=path.name,
                    content=content,
                )
            )
        return files, ""
