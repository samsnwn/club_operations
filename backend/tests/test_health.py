"""FastAPI TestClient-based API tests."""

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.base import get_db
from app.main import app

client = TestClient(app)

HEALTH_OK = {"status": "ok", "database": "ok"}
HEALTH_DEGRADED = {"status": "degraded", "database": "error"}


def test_health_returns_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == HEALTH_OK


class _UnreachableSession:
    """Session stand-in whose every query fails like a lost database."""

    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("simulated db outage"))


def test_health_returns_503_when_database_fails() -> None:
    app.dependency_overrides[get_db] = lambda: _UnreachableSession()
    try:
        response = client.get("/api/v1/health")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 503
    assert response.json() == HEALTH_DEGRADED
    assert "simulated db outage" not in response.text
