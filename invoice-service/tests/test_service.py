# Invoice service — API + pipeline tests against a temporary SQLite store.

import os
import time
from pathlib import Path
from tempfile import mkdtemp

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import DEFAULT_INTERNAL_TOKEN, get_settings
from app.db.base import Base, SessionLocal, engine
from app.ingestion.fixtures import FixtureSource
from app.api.v1 import invoices as invoice_routes
from app.ingestion import pipeline
from app.ingestion.pipeline import ingest_file, poll_sources
from app.main import create_app
from app.models.invoice import Invoice
from app.notify.digest import build_digest
from app.review.routes import MAX_REVIEWER_LENGTH


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
    monkeypatch.setenv("INVOICE_ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    get_settings.cache_clear()
    Base.metadata.create_all(engine)

    return TestClient(create_app())


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


def test_queue_rejects_unknown_bearer_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/queue", headers={"Authorization": "Bearer not-the-token"}
    )
    assert response.status_code == 401


def test_legacy_review_tokens_are_ignored(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The per-user token path was removed; the old env var has no effect."""
    monkeypatch.setenv("INVOICE_REVIEW_TOKENS", '{"owner": "legacy-owner-token"}')
    get_settings.cache_clear()
    try:
        response = client.get(
            "/api/v1/queue",
            headers={"Authorization": "Bearer legacy-owner-token"},
        )
        assert response.status_code == 401
    finally:
        get_settings.cache_clear()


def test_production_refuses_development_internal_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INVOICE_ENVIRONMENT", "production")
    monkeypatch.setenv("INVOICE_INTERNAL_TOKEN", DEFAULT_INTERNAL_TOKEN)
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="development internal token"):
            create_app()
    finally:
        get_settings.cache_clear()


def test_production_accepts_unique_internal_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INVOICE_ENVIRONMENT", "production")
    monkeypatch.setenv("INVOICE_INTERNAL_TOKEN", "unique-production-token")
    get_settings.cache_clear()
    try:
        assert create_app().title == "Blue Velvet Invoice Service"
    finally:
        get_settings.cache_clear()


def test_empty_internal_token_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INVOICE_ENVIRONMENT", "production")
    monkeypatch.setenv("INVOICE_INTERNAL_TOKEN", "")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="must not be empty"):
            create_app()
    finally:
        get_settings.cache_clear()


# The minimum a reviewer must supply before a row may be confirmed.
VALID_REVIEW = {
    "supplier": "Musterveu GmbH",
    "invoice_date": "2026-11-01",
    "gross": 1190.00,
}


def _first_queue_item(client: TestClient) -> dict:
    return client.get(
        "/api/v1/queue",
        headers={"Authorization": f"Bearer {get_settings().internal_token}"},
    ).json()["items"][0]


def test_facade_reviewer_header_marks_confirming_user(
    client: TestClient, db: Session
) -> None:
    """The backend facade sends the authenticated username; confirm records it."""
    run_fixture_ingest(db)
    target = _first_queue_item(client)
    response = client.post(
        f"/api/v1/queue/{target['id']}/confirm",
        headers={
            "Authorization": f"Bearer {get_settings().internal_token}",
            "X-Reviewer": "owner",
        },
        json=VALID_REVIEW,
    )
    assert response.status_code == 200
    assert response.json()["reviewed_by"] == "owner"
    db.expire_all()
    assert db.get(Invoice, target["id"]).reviewed_by == "owner"


def test_internal_token_without_reviewer_header_is_backend(
    client: TestClient, db: Session
) -> None:
    """Scheduled/system actions carry no user identity and stay attributed."""
    run_fixture_ingest(db)
    target = _first_queue_item(client)
    response = client.post(
        f"/api/v1/queue/{target['id']}/confirm",
        headers={"Authorization": f"Bearer {get_settings().internal_token}"},
        json=VALID_REVIEW,
    )
    assert response.json()["reviewed_by"] == "backend"


def test_reviewer_header_alone_does_not_authenticate(client: TestClient) -> None:
    assert (
        client.get("/api/v1/queue", headers={"X-Reviewer": "owner"}).status_code == 401
    )


def test_reviewer_header_is_trimmed_and_capped(client: TestClient, db: Session) -> None:
    """The forwarded name is normalised and fits `reviewed_by` (String(64))."""
    run_fixture_ingest(db)
    target = _first_queue_item(client)
    response = client.post(
        f"/api/v1/queue/{target['id']}/confirm",
        headers={
            "Authorization": f"Bearer {get_settings().internal_token}",
            "X-Reviewer": f"  {'x' * 100}  ",
        },
        json=VALID_REVIEW,
    )
    assert response.json()["reviewed_by"] == "x" * MAX_REVIEWER_LENGTH


def test_review_flow_confirm_with_corrections(client: TestClient, db: Session) -> None:
    run_fixture_ingest(db)
    auth = {"Authorization": f"Bearer {get_settings().internal_token}"}
    items = client.get("/api/v1/queue", headers=auth).json()["items"]
    target = items[0]
    response = client.post(
        f"/api/v1/queue/{target['id']}/confirm",
        headers={**auth, "X-Reviewer": "admin"},
        json={**VALID_REVIEW, "supplier": "Musterveru GmbH"},
    )
    assert response.json() == {
        "id": target["id"],
        "status": "confirmed",
        "reviewed_by": "admin",
    }
    assert client.get("/api/v1/queue", headers=auth).json()["count"] == len(items) - 1


def test_digest_lists_pending(db: Session) -> None:
    run_fixture_ingest(db)
    body = build_digest(db)
    assert "review" in body
    assert "Not recognised automatically" in body


def _age_file(path: Path, seconds: float) -> None:
    """Pretend the file has been untouched for `seconds` (settled capture)."""
    then = time.time() - seconds
    os.utime(path, (then, then))


def test_internal_import_requires_internal_token(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INVOICE_INBOX_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        assert client.post("/api/v1/internal/invoices/import").status_code == 401
    finally:
        get_settings.cache_clear()


def test_internal_import_ingests_settled_inbox(
    client: TestClient, db: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Endpoint-level drop-folder flow: settled file → review row, and a
    second import is a content-hash no-op."""
    invoice_file = tmp_path / "2026-11-04-muster.txt"
    invoice_file.write_bytes(
        b"Musterveu GmbH\nRechnungs-Nr: 2026-118\nNetto: 1.000,00\nGesamt: 1.190,00\n"
    )
    _age_file(invoice_file, 7200.0)
    monkeypatch.setenv("INVOICE_INBOX_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        headers = {"Authorization": f"Bearer {get_settings().internal_token}"}
        assert client.post(
            "/api/v1/internal/invoices/import", headers=headers
        ).json() == {"new_invoices": 1}
        assert client.post(
            "/api/v1/internal/invoices/import", headers=headers
        ).json() == {"new_invoices": 0}
    finally:
        get_settings.cache_clear()
    assert db.query(Invoice).count() == 1


def test_internal_token_can_review(client: TestClient) -> None:
    """The facade holds only the internal token; it may review through the
    queue endpoints, with attribution supplied by `X-Reviewer`."""
    headers = {"Authorization": f"Bearer {get_settings().internal_token}"}
    assert client.get("/api/v1/queue", headers=headers).status_code == 200


def test_internal_original_requires_internal_token(client: TestClient) -> None:
    assert client.get("/api/v1/internal/invoices/1/original").status_code == 401


def test_internal_original_unknown_invoice(client: TestClient) -> None:
    headers = {"Authorization": f"Bearer {get_settings().internal_token}"}
    assert (
        client.get(
            "/api/v1/internal/invoices/9999/original", headers=headers
        ).status_code
        == 404
    )


def test_internal_original_serves_stored_capture(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = b"%PDF-1.5 handwritten test capture"
    monkeypatch.setenv("INVOICE_ATTACHMENTS_DIR", str(mkdtemp()))
    get_settings.cache_clear()
    try:
        assert ingest_file(db, CapturedTestFile(content))
        invoice = db.query(Invoice).one()
        headers = {"Authorization": f"Bearer {get_settings().internal_token}"}
        response = client.get(
            f"/api/v1/internal/invoices/{invoice.id}/original", headers=headers
        )
        assert response.status_code == 200
        assert response.content == content
        assert response.headers["content-type"] == "application/pdf"
    finally:
        get_settings.cache_clear()


def _auth() -> dict:
    return {"Authorization": f"Bearer {get_settings().internal_token}"}


def test_confirm_requires_the_minimum_fields(client: TestClient, db: Session) -> None:
    """An empty review must never produce an export-eligible row."""
    run_fixture_ingest(db)
    target = _first_queue_item(client)
    response = client.post(
        f"/api/v1/queue/{target['id']}/confirm",
        headers=_auth(),
        json={"supplier": "   ", "gross": 10.0},
    )
    assert response.status_code == 422
    assert "supplier" in response.json()["detail"]
    assert "invoice_date" in response.json()["detail"]
    db.expire_all()
    assert db.get(Invoice, target["id"]).status != "confirmed"


def test_rejected_invoice_cannot_be_confirmed(client: TestClient, db: Session) -> None:
    run_fixture_ingest(db)
    target = _first_queue_item(client)
    url = f"/api/v1/queue/{target['id']}"
    assert client.post(f"{url}/reject", headers=_auth()).status_code == 200
    response = client.post(f"{url}/confirm", headers=_auth(), json=VALID_REVIEW)
    assert response.status_code == 409
    assert response.json()["detail"] == "Already rejected"
    db.expire_all()
    invoice = db.get(Invoice, target["id"])
    assert invoice.status == "rejected"
    assert invoice.supplier_final is None


def test_confirmed_invoice_cannot_be_reviewed_again(
    client: TestClient, db: Session
) -> None:
    run_fixture_ingest(db)
    target = _first_queue_item(client)
    url = f"/api/v1/queue/{target['id']}"
    first = {**_auth(), "X-Reviewer": "owner"}
    second = {**_auth(), "X-Reviewer": "admin"}
    assert client.post(f"{url}/confirm", headers=first, json=VALID_REVIEW).is_success
    assert (
        client.post(f"{url}/confirm", headers=second, json=VALID_REVIEW).status_code
        == 409
    )
    assert client.post(f"{url}/reject", headers=second).status_code == 409
    db.expire_all()
    invoice = db.get(Invoice, target["id"])
    assert (invoice.status, invoice.reviewed_by) == ("confirmed", "owner")


def test_one_failing_file_does_not_abort_the_run(
    db: Session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("INVOICE_ATTACHMENTS_DIR", str(tmp_path))
    get_settings.cache_clear()
    real_extract = pipeline.field_parser.extract_fields
    calls = {"count": 0}

    def flaky(text: str):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("boom")
        return real_extract(text)

    monkeypatch.setattr(pipeline.field_parser, "extract_fields", flaky)
    try:
        # First fixture fails, the other two still land.
        assert run_fixture_ingest(db) == 2
        # The watermark did not advance past the failure, so it is retried.
        assert run_fixture_ingest(db) == 1
    finally:
        get_settings.cache_clear()
    assert db.query(Invoice).count() == 3


def test_duplicate_is_skipped_before_pdf_parsing(
    db: Session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("INVOICE_ATTACHMENTS_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        capture = CapturedTestFile(b"%PDF-1.5 handwritten test capture")
        assert ingest_file(db, capture) is True

        def no_parse(content: bytes) -> int:
            raise AssertionError("an already-ingested PDF must not be re-parsed")

        monkeypatch.setattr(pipeline.text_extractor, "pdf_page_count", no_parse)
        assert ingest_file(db, capture) is False
    finally:
        get_settings.cache_clear()


def test_concurrent_import_is_refused(client: TestClient) -> None:
    assert invoice_routes._import_lock.acquire(blocking=False)
    try:
        response = client.post("/api/v1/internal/invoices/import", headers=_auth())
    finally:
        invoice_routes._import_lock.release()
    assert response.status_code == 409
    assert response.json()["detail"] == "An import is already running"
