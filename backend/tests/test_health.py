"""FastAPI TestClient-based API tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

HEALTH_OK = {"status": "ok", "database": "ok"}


def test_health_returns_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == HEALTH_OK


def test_root_health_alias_returns_ok() -> None:
    """Local tooling probes /health at the root; it must not 404."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == HEALTH_OK


def test_root_health_alias_hidden_from_schema() -> None:
    """/health is an alias, not part of the documented API surface."""
    schema = client.get("/openapi.json").json()
    assert "/api/v1/health" in schema["paths"]
    assert "/health" not in schema["paths"]
