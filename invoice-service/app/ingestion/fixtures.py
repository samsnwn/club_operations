"""Fixture ingestion source — clearly fake club data for development/tests.

Feeds the pipeline locally until real Gmail/Drive credentials exist, and keeps
the corpus reproducible for tests (hard rule 3: no real club data ever).
"""

from dataclasses import dataclass
from pathlib import Path

from app.ingestion.base import CapturedFile

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "invoices"


@dataclass(frozen=True)
class FixtureCapturedFile:
    source: str
    filename: str
    content: bytes


class FixtureSource:
    name = "fixture"

    def poll(self, cursor: str | None) -> tuple[list[CapturedFile], str]:
        """Return fixture files with names later than the cursor (name sorts as
        the catch-up watermark), mirroring real catch-up semantics."""
        files: list[CapturedFile] = []
        newest = cursor or ""
        if FIXTURES_DIR.exists():
            for path in sorted(FIXTURES_DIR.iterdir()):
                if path.name > newest and path.is_file():
                    files.append(
                        FixtureCapturedFile(
                            source=self.name,
                            filename=path.name,
                            content=path.read_bytes(),
                        )
                    )
                    newest = path.name
        return files, newest
