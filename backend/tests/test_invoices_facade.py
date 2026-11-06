# Invoice facade tests against a mocked invoice-service transport.
#
# The facade's HTTP layer is exercised through httpx.MockTransport via the
# `_client()` test seam: request paths, forwarded auth headers, queue merge
# ordering and error mapping are all asserted against recorded requests.

from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import invoices
from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def _use_service(monkeypatch: pytest.MonkeyPatch, handler: Any) -> None:
    """Point the facade at a mock invoice-service for this test."""

    def factory() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(invoices, "_client", factory)


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
        seen["path"] = request.url.path
        return httpx.Response(200, json={"count": 0, "items": []})

    _use_service(monkeypatch, handler)
    assert client.get("/api/v1/invoices/queue?status=pending_review").status_code == 200
    assert seen["path"] == "/api/v1/queue"
    assert seen["authorization"] == f"Bearer {get_settings().invoice_service_token}"


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
