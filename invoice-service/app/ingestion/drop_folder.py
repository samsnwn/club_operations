"""Local drop-folder ingestion for the first real-invoice demonstration."""

from dataclasses import dataclass
from pathlib import Path

from app.ingestion.base import CapturedFile


@dataclass(frozen=True)
class DropFolderCapturedFile:
    source: str
    filename: str
    content: bytes


class DropFolderSource:
    name = "drop_folder"

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def poll(self, cursor: str | None) -> tuple[list[CapturedFile], str]:
        files: list[CapturedFile] = []
        if not self.directory.exists():
            return files, ""
        for path in sorted(self.directory.iterdir()):
            if path.is_file():
                files.append(
                    DropFolderCapturedFile(
                        source=self.name,
                        filename=path.name,
                        content=path.read_bytes(),
                    )
                )
        return files, ""
