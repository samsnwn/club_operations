# Drop-folder source tests: settle/stability rules, hidden files, size limit.
#
# Timing does not rely on wall-clock luck: tests pin the settle window high and
# control modification times explicitly (os.utime), so "fresh" and "old" are
# unambiguous regardless of test-run latency.

import os
import time
from pathlib import Path

from app.ingestion.drop_folder import DropFolderSource


def _age_file(path: Path, seconds: float) -> None:
    """Pretend the file has been untouched for `seconds`."""
    then = time.time() - seconds
    os.utime(path, (then, then))


def _source(directory: Path) -> DropFolderSource:
    return DropFolderSource(directory, max_attachment_bytes=1024, settle_seconds=3600)


def test_captures_only_settled_invoice_files(tmp_path: Path) -> None:
    """Settled files are captured; dotfiles and subdirectories never are."""
    (tmp_path / ".DS_Store").write_bytes(b"finder noise")
    (tmp_path / "notes").mkdir()
    invoice = tmp_path / "2026-11-04-muster.txt"
    invoice.write_bytes(b"Musterveu GmbH invoice")
    _age_file(invoice, 7200.0)  # long-untouched: settled on first observation

    files = _source(tmp_path).poll()

    assert [(f.filename, f.content) for f in files] == [
        ("2026-11-04-muster.txt", b"Musterveu GmbH invoice")
    ]


def test_unsettled_file_is_never_captured_while_copying(tmp_path: Path) -> None:
    """Partial-write race: a file observed mid-copy is recorded but withheld
    until it has stopped changing; when captured, it is the complete file."""
    source = _source(tmp_path)
    target = tmp_path / "invoice.txt"

    target.write_bytes(b"part")  # as if the copy were still in flight
    _age_file(target, 30.0)  # fresh enough for the settle window
    assert source.poll() == []

    target.write_bytes(b"part-complete")  # copy progresses between polls
    _age_file(target, 30.0)
    assert source.poll() == []

    _age_file(target, 7200.0)  # copy finished and settled
    files = source.poll()
    assert [(f.filename, f.content) for f in files] == [
        ("invoice.txt", b"part-complete")
    ]


def test_stable_file_captures_via_two_unchanged_observations(tmp_path: Path) -> None:
    """A file that stopped writing after the last poll captures on the next
    poll even though it is still inside the settle window."""
    source = _source(tmp_path)
    target = tmp_path / "invoice.txt"
    target.write_bytes(b"Musterveu GmbH")

    assert source.poll() == []  # observed, not settled yet

    files = source.poll()  # unchanged since the observation → captured
    assert [f.content for f in files] == [b"Musterveu GmbH"]


def test_oversized_files_are_skipped(tmp_path: Path) -> None:
    """Files above the capture limit are dropped by the source, not read into
    memory first (ingest_file re-checks as the generic backstop)."""
    big = tmp_path / "huge.txt"
    big.write_bytes(b"x" * 11)
    _age_file(big, 7200.0)

    source = DropFolderSource(tmp_path, max_attachment_bytes=10)
    assert source.poll() == []
