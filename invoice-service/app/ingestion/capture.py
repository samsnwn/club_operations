"""A capture: one file taken in from an ingestion channel (see GLOSSARY.md).

Both ingestion channels — the invoice folder on Google Drive and the local
inbox — produce `CapturedFile`s for `pipeline.import_from`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapturedFile:
    source: str
    filename: str
    content: bytes
    # Where the original lives in its channel (the Drive file ID), if anywhere.
    source_ref: str | None = None
