# Invoice service — API + pipeline tests against a temporary SQLite store.

import os
from pathlib import Path
from tempfile import mkdtemp

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("INVOICE_DATABASE_URL", "sqlite:///:memory:")  # pragma: env-safe

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base, SessionLocal, engine
from app.ingestion.fixtures import FixtureSource
from app.ingestion.pipeline import ingest_file, poll_sources
from app.models.invoice import Invoice
from app.notify.digest import build_digest

OWNER_TOKEN = "owner-test-token"
ADMIN_TOKEN = "admin-test-token"


class CapturedTestFile:
    source = "test"
    filename = "oversized.txt"

    def __init__(self, content: bytes) -> None:
        self.content = content


@pytest.fixture(name="db")
def db_fixture() -> Session:
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv(
        "INVOICE_REVIEW_TOKENS",
        f'{{"owner": "{OWNER_TOKEN}", "admin": "{ADMIN_TOKEN}"}}',
    )
    monkeypatch.setenv("INVOICE_ATTACHMENTS_DIR", str(mkdtemp()))
    get_settings.cache_clear()
    Base.metadata.create_all(engine)
    from app.main import create_app as make

    return TestClient(make())


def run_fixture_ingest(db: Session) -> int:
    return poll_sources(db, [FixtureSource()])


def test_health(client: TestClient) -> None:
    assert client.get("/api/v1/health").json() == {"status": "ok", "database": "ok"}


def test_ingest_queues_and_dedupes(db: Session) -> None:
    assert run_fixture_ingest(db) == 3
    # Watermark-based catch-up: second run adds nothing (all consumed).
    assert run_fixture_ingest(db) == 0
    statuses = {row.status for row in db.query(Invoice).all()}
    assert statuses == {"pending_review", "needs_attention"}


def test_unrecognised_capture_becomes_needs_attention(db: Session) -> None:
    run_fixture_ingest(db)
    attention = db.query(Invoice).filter(Invoice.status == "needs_attention").one()
    assert attention.supplier_guess is None


def test_oversized_capture_is_rejected_before_storage(
    db: Session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("INVOICE_MAX_ATTACHMENT_BYTES", "10")
    monkeypatch.setenv("INVOICE_ATTACHMENTS_DIR", str(tmp_path))
    get_settings.cache_clear()

    assert ingest_file(db, CapturedTestFile(b"x" * 11)) is False
    assert db.query(Invoice).count() == 0
    assert list(tmp_path.iterdir()) == []


def test_queue_requires_token(client: TestClient) -> None:
    assert client.get("/api/v1/queue").status_code == 401


def test_review_flow_confirm_with_corrections(client: TestClient, db: Session) -> None:
    run_fixture_ingest(db)
    items = client.get(
        "/api/v1/queue", headers={"Authorization": f"Bearer {OWNER_TOKEN}"}
    ).json()["items"]
    target = items[0]
    response = client.post(
        f"/api/v1/queue/{target['id']}/confirm",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
        json={"gross": 1190.00, "supplier": "Musterveru GmbH"},
    )
    assert response.json() == {
        "id": target["id"],
        "status": "confirmed",
        "reviewed_by": "admin",
    }
    assert (
        client.get(
            "/api/v1/queue", headers={"Authorization": f"Bearer {OWNER_TOKEN}"}
        ).json()["count"]
        == len(items) - 1
    )


def test_digest_lists_pending(db: Session) -> None:
    run_fixture_ingest(db)
    body = build_digest(db)
    assert "review" in body
    assert "Not recognised automatically" in body
