# Invoice facade tests against a mocked invoice-service transport.
#
# The facade's HTTP layer is exercised through httpx.MockTransport via the
# `_client()` test seam: request paths, forwarded auth headers, queue merge
# ordering and error mapping are all asserted against recorded requests.

import json
from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import invoices
from app.auth.dependencies import current_user
from app.core.config import get_settings
from app.main import app
from app.models import User

TEST_USER = User(
    id=1,
    username="tester",
    password_hash="unused",
    role="owner",
    is_active=True,
    must_change_password=False,
)


@pytest.fixture(autouse=True)
def _authenticated() -> Iterator[None]:
    """Facade behaviour is tested independently of the login flow."""
    app.dependency_overrides[current_user] = lambda: TEST_USER
    yield
    app.dependency_overrides.pop(current_user, None)


client = TestClient(app)


def _use_service(monkeypatch: pytest.MonkeyPatch, handler: Any) -> None:
    """Point the facade at a mock invoice-service for this test."""

    def factory() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(invoices, "_client", factory)


def test_staff_cannot_reach_invoice_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Staff accounts may sign in, but invoice data is owner/admin only."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("the invoice service must not be called for staff")

    _use_service(monkeypatch, handler)
    staff = User(
        id=2,
        username="staffer",
        password_hash="unused",
        role="staff",
        is_active=True,
        must_change_password=False,
    )
    app.dependency_overrides[current_user] = lambda: staff
    try:
        assert client.get("/api/v1/invoices/queue").status_code == 403
        assert client.post("/api/v1/invoices/import").status_code == 403
    finally:
        app.dependency_overrides[current_user] = lambda: TEST_USER


def test_admin_can_reach_invoice_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"count": 0, "items": []})

    _use_service(monkeypatch, handler)
    admin = User(
        id=3,
        username="admin1",
        password_hash="unused",
        role="admin",
        is_active=True,
        must_change_password=False,
    )
    app.dependency_overrides[current_user] = lambda: admin
    try:
        assert (
            client.get("/api/v1/invoices/queue?status=pending_review").status_code
            == 200
        )
    finally:
        app.dependency_overrides[current_user] = lambda: TEST_USER


def test_queue_merges_statuses_confident_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The merged 'all' view must mirror the service's order: confidence
    descending, oldest first within a confidence tie — not per-status order
    simply concatenated."""
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url.params["status"]))
        items = {
            "pending_review": [
                {"confidence": 0.9, "created_at": "2026-11-05T10:00"},
                {"confidence": 0.7, "created_at": "2026-11-05T09:00"},
                # Same confidence, deliberately newest-first in input.
                {"confidence": 0.8, "created_at": "2026-11-05T15:00"},
                {"confidence": 0.8, "created_at": "2026-11-05T08:00"},
            ],
            "needs_attention": [
                {"confidence": 0.99, "created_at": "2026-11-05T07:00"},
            ],
        }.get(str(request.url.params["status"]), [])
        return httpx.Response(200, json={"count": len(items), "items": items})

    _use_service(monkeypatch, handler)
    response = client.get("/api/v1/invoices/queue")

    assert response.status_code == 200
    body = response.json()
    assert [item["confidence"] for item in body["items"]] == [0.99, 0.9, 0.8, 0.8, 0.7]
    assert [item["created_at"] for item in body["items"][2:4]] == [
        "2026-11-05T08:00",
        "2026-11-05T15:00",
    ]
    assert requested == ["pending_review", "needs_attention"]
    assert body["count"] == 5


def test_queue_single_status_passes_status_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url.params["status"]))
        return httpx.Response(200, json={"count": 0, "items": []})

    _use_service(monkeypatch, handler)
    assert (
        client.get("/api/v1/invoices/queue?status=needs_attention").status_code == 200
    )
    assert requested == ["needs_attention"]


def test_facade_forwards_internal_service_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")
        seen["reviewer"] = request.headers.get("x-reviewer")
        seen["path"] = request.url.path
        return httpx.Response(200, json={"count": 0, "items": []})

    _use_service(monkeypatch, handler)
    assert client.get("/api/v1/invoices/queue?status=pending_review").status_code == 200
    assert seen["path"] == "/api/v1/queue"
    assert seen["authorization"] == f"Bearer {get_settings().invoice_service_token}"
    assert seen["reviewer"] == "tester"


def test_facade_ignores_client_supplied_reviewer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["reviewer"] = request.headers.get("x-reviewer")
        return httpx.Response(200, json={"count": 0, "items": []})

    _use_service(monkeypatch, handler)
    response = client.get(
        "/api/v1/invoices/queue?status=pending_review",
        headers={"X-Reviewer": "someone-else"},
    )

    assert response.status_code == 200
    assert seen["reviewer"] == "tester"


def test_confirm_forwards_reviewer_and_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["reviewer"] = request.headers.get("x-reviewer")
        seen["path"] = request.url.path
        seen["json"] = request.content
        return httpx.Response(
            200, json={"id": 7, "status": "confirmed", "reviewed_by": "tester"}
        )

    _use_service(monkeypatch, handler)
    response = client.post(
        "/api/v1/invoices/7/confirm", json={"gross": 1190.0, "supplier": "Muster"}
    )

    assert response.status_code == 200
    assert response.json()["reviewed_by"] == "tester"
    assert seen["reviewer"] == "tester"
    assert seen["path"] == "/api/v1/queue/7/confirm"
    assert json.loads(seen["json"]) == {"gross": 1190.0, "supplier": "Muster"}


def test_import_hits_internal_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if (
            request.method == "POST"
            and request.url.path == "/api/v1/internal/invoices/import"
        ):
            return httpx.Response(200, json={"new_invoices": 2})
        return httpx.Response(500, text="unexpected call")

    _use_service(monkeypatch, handler)
    assert client.post("/api/v1/invoices/import").json() == {"new_invoices": 2}


def test_unavailable_service_maps_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    _use_service(monkeypatch, handler)
    response = client.get("/api/v1/invoices/queue?status=pending_review")
    assert response.status_code == 503
    assert response.json()["detail"] == "Invoice service unavailable"


def test_upstream_error_status_is_passed_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Invoice not found"})

    _use_service(monkeypatch, handler)
    response = client.get("/api/v1/invoices/123")
    assert response.status_code == 404
    assert "Invoice not found" in response.json()["detail"]


def test_original_streamed_inline(monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = b"%PDF-1.5 handwritten test capture"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        return httpx.Response(
            200, content=pdf, headers={"content-type": "application/pdf"}
        )

    _use_service(monkeypatch, handler)
    response = client.get("/api/v1/invoices/7/original")
    assert response.status_code == 200
    assert response.content == pdf
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == "inline"
