"""Capture sources and the ingest pipeline.

Design (README §Phase 0.5 + interim hosting plan A): both channels are
pull-based catch-up pollers driven by per-source sync watermarks, so offline
periods simply become a bigger backlog on the next run. The forwarding mailbox
and the Drive folder are the buffers — the service never needs to be online
when an invoice arrives.
"""

from typing import Protocol


class CapturedFile(Protocol):
    """One file caught by a source, before de-duplication."""

    source: str
    filename: str
    content: bytes


class IngestionSource(Protocol):
    """A catch-up poller over one ingestion channel."""

    name: str

    def poll(self, cursor: str | None) -> tuple[list[CapturedFile], str]:
        """Return captured files and the new cursor value."""
        ...
