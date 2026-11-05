"""FastAPI TestClient-based API tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

HEALTH_OK = {"status": "ok", "database": "ok"}


def test_health_returns_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == HEALTH_OK
