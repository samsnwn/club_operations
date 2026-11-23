# Invoice-folder (Google Drive) tests against a fake Drive: no network, a
# throwaway key generated per test run, deliberately fake file contents.

import hashlib
import json
from pathlib import Path

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base, SessionLocal, engine
from app.ingestion import pipeline
from app.ingestion.drive import DriveAccessRefused, DriveSource, DriveUnavailable
from app.main import create_app
from app.models.invoice import Invoice

INVOICE_TEXT = b"Musterveu GmbH\nRechnungsdatum: 04.11.2026\nGesamt: 1.190,00\n"


def _md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


@pytest.fixture(name="credentials", scope="module")
def credentials_fixture(tmp_path_factory: pytest.TempPathFactory) -> Path:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    path = tmp_path_factory.mktemp("secrets") / "service-account.json"
    path.write_text(
        json.dumps(
            {
                "type": "service_account",
                "client_email": "invoices@example-project.iam.gserviceaccount.test",
                "private_key_id": "test",
                "private_key": pem,
            }
        )
    )
    return path


@pytest.fixture(name="db")
def db_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Session:
    monkeypatch.setenv("INVOICE_ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    get_settings.cache_clear()
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)
        get_settings.cache_clear()


class FakeDrive:
    """Token endpoint + folder listing (paged) + downloads."""

    def __init__(self, files: list[dict], page_size: int = 100) -> None:
        self.files = files
        self.page_size = page_size
        self.downloads: list[str] = []
        self.list_status = 200

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth2.googleapis.com":
            assert b"jwt-bearer" in request.content
            return httpx.Response(200, json={"access_token": "fake-token"})
        assert request.headers["authorization"] == "Bearer fake-token"
        if request.url.path == "/drive/v3/files":
            if self.list_status != 200:
                return httpx.Response(self.list_status, json={"error": "no"})
            start = int(request.url.params.get("pageToken", "0"))
            page = self.files[start : start + self.page_size]
            body: dict = {"files": [self._metadata(item) for item in page]}
            if start + self.page_size < len(self.files):
                body["nextPageToken"] = str(start + self.page_size)
            return httpx.Response(200, json=body)
        file_id = request.url.path.rsplit("/", 1)[-1]
        self.downloads.append(file_id)
        item = next(item for item in self.files if item["id"] == file_id)
        if item.get("broken"):
            return httpx.Response(500)
        return httpx.Response(200, content=item["content"])

    @staticmethod
    def _metadata(item: dict) -> dict:
        metadata = {key: item[key] for key in ("id", "name", "mimeType")}
        if "content" in item:
            metadata["size"] = str(item.get("size", len(item["content"])))
            metadata["md5Checksum"] = _md5(item["content"])
        return metadata

    def source(self, credentials: Path, max_bytes: int = 1024) -> DriveSource:
        return DriveSource(
            "fake-folder-id",
            credentials,
            max_attachment_bytes=max_bytes,
            transport=httpx.MockTransport(self.handler),
        )


def _file(file_id: str, mime_type: str, content: bytes | None = None) -> dict:
    item = {"id": file_id, "name": file_id, "mimeType": mime_type}
    return item if content is None else {**item, "content": content}


def _pdf(file_id: str, content: bytes, **extra) -> dict:
    return {
        "id": file_id,
        "name": f"{file_id}.pdf",
        "mimeType": "application/pdf",
        "content": content,
        **extra,
    }


def test_poll_downloads_only_new_acceptable_files(credentials: Path) -> None:
    drive = FakeDrive(
        [
            _pdf("new", b"%PDF new invoice"),
            _pdf("known", b"%PDF already imported"),
            _file("photo", "image/png", b"p"),
            _file("sub", "application/vnd.google-apps.folder"),  # no MD5
            _file("doc", "application/vnd.google-apps.document"),  # no MD5
            _file("zip", "application/zip", b"z"),
            _pdf("huge", b"%PDF", size=4096),
        ]
    )
    known = {_md5(b"%PDF already imported")}

    captures = drive.source(credentials).poll(lambda md5: md5 in known)

    assert [(c.source, c.source_ref, c.filename) for c in captures] == [
        ("drive", "new", "new.pdf"),
        ("drive", "photo", "photo"),
    ]
    assert drive.downloads == ["new", "photo"]  # known file never downloaded


def test_poll_follows_pages(credentials: Path) -> None:
    drive = FakeDrive([_pdf(f"f{n}", f"%PDF {n}".encode()) for n in range(5)], 2)
    captures = drive.source(credentials).poll(lambda _: False)
    assert [c.source_ref for c in captures] == ["f0", "f1", "f2", "f3", "f4"]


def test_one_failed_download_does_not_stop_the_others(credentials: Path) -> None:
    drive = FakeDrive([_pdf("bad", b"%PDF a", broken=True), _pdf("ok", b"%PDF b")])
    captures = drive.source(credentials).poll(lambda _: False)
    assert [c.source_ref for c in captures] == ["ok"]


def test_folder_not_shared_is_refused(credentials: Path) -> None:
    drive = FakeDrive([])
    drive.list_status = 404
    with pytest.raises(DriveAccessRefused, match="shared with the service account"):
        drive.source(credentials).poll(lambda _: False)


def test_drive_server_error_is_unavailable(credentials: Path) -> None:
    drive = FakeDrive([])
    drive.list_status = 503
    with pytest.raises(DriveUnavailable):
        drive.source(credentials).poll(lambda _: False)


def test_unreachable_drive_is_unavailable(credentials: Path) -> None:
    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    source = DriveSource(
        "fake-folder-id",
        credentials,
        max_attachment_bytes=1024,
        transport=httpx.MockTransport(offline),
    )
    with pytest.raises(DriveUnavailable):
        source.poll(lambda _: False)


def test_missing_credentials_file_is_refused(tmp_path: Path) -> None:
    source = DriveSource(
        "fake-folder-id", tmp_path / "absent.json", max_attachment_bytes=1024
    )
    with pytest.raises(DriveAccessRefused, match="credentials file"):
        source.poll(lambda _: False)


def test_import_skips_drive_files_already_imported(
    db: Session, credentials: Path
) -> None:
    """Re-runs and duplicate uploads are skipped by MD5 without downloading."""
    drive = FakeDrive(
        [_pdf("first", INVOICE_TEXT), _pdf("second-upload", INVOICE_TEXT)]
    )
    source = drive.source(credentials, max_bytes=get_settings().max_attachment_bytes)

    assert pipeline.import_from(db, source) == 1  # same content uploaded twice
    drive.downloads.clear()
    assert pipeline.import_from(db, source) == 0
    assert drive.downloads == []

    invoice = db.query(Invoice).one()
    assert (invoice.source, invoice.source_ref) == ("drive", "first")
    assert invoice.content_md5 == _md5(INVOICE_TEXT)
    assert invoice.status == "pending_review"


def test_legacy_row_learns_its_md5_on_recapture(db: Session) -> None:
    """Rows from before MD5 tracking stop being re-downloaded after one pass."""
    db.add(
        Invoice(
            source="drop_folder",
            content_hash=hashlib.sha256(INVOICE_TEXT).hexdigest(),
            status="pending_review",
        )
    )
    db.commit()
    capture = pipeline.CapturedFile("drive", "again.pdf", INVOICE_TEXT, "id-1")
    assert pipeline.ingest_file(db, capture) is False
    db.expire_all()
    assert db.query(Invoice).one().content_md5 == _md5(INVOICE_TEXT)


def test_import_uses_drive_when_configured(
    db: Session, monkeypatch: pytest.MonkeyPatch, credentials: Path
) -> None:
    monkeypatch.setenv("INVOICE_DRIVE_FOLDER_ID", "fake-folder-id")
    monkeypatch.setenv("INVOICE_DRIVE_CREDENTIALS_FILE", str(credentials))
    get_settings.cache_clear()
    used: list[str] = []

    class RecordingDrive:
        def __init__(self, folder_id: str, credentials_file: str, **_: object):
            used.append(folder_id)

        def poll(self, is_known: object) -> list:
            return []

    monkeypatch.setattr(pipeline, "DriveSource", RecordingDrive)
    assert pipeline.import_invoices(db) == 0
    assert used == ["fake-folder-id"]


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (DriveUnavailable("Google Drive unavailable"), 503),
        (DriveAccessRefused("Google Drive access refused"), 502),
    ],
)
def test_import_endpoint_reports_drive_failures(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int
) -> None:
    def failing(db: Session) -> int:
        raise error

    monkeypatch.setattr(pipeline, "import_invoices", failing)
    get_settings.cache_clear()
    Base.metadata.create_all(engine)
    try:
        response = TestClient(create_app()).post(
            "/api/v1/internal/invoices/import",
            headers={"Authorization": f"Bearer {get_settings().internal_token}"},
        )
    finally:
        Base.metadata.drop_all(engine)
    assert response.status_code == status
    assert response.json()["detail"] == str(error)


def test_file_over_the_page_limit_is_not_downloaded_again(
    db: Session, credentials: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rejection that cannot change on a retry is remembered by MD5."""
    monkeypatch.setattr(pipeline.text_extractor, "pdf_page_count", lambda _: 999)
    drive = FakeDrive([_pdf("long", b"%PDF-1.4 fake long document")])
    source = drive.source(credentials, max_bytes=get_settings().max_attachment_bytes)

    assert pipeline.import_from(db, source) == 0
    assert drive.downloads == ["long"]
    drive.downloads.clear()
    assert pipeline.import_from(db, source) == 0
    assert drive.downloads == []
    assert db.query(Invoice).count() == 0


def test_failed_download_is_retried_on_the_next_import(
    db: Session, credentials: Path
) -> None:
    """Transient failures are never remembered as rejections."""
    drive = FakeDrive([_pdf("flaky", INVOICE_TEXT, broken=True)])
    source = drive.source(credentials, max_bytes=get_settings().max_attachment_bytes)

    assert pipeline.import_from(db, source) == 0
    drive.downloads.clear()
    assert pipeline.import_from(db, source) == 0
    assert drive.downloads == ["flaky"]
