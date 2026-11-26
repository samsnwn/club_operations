# Behind the dev Caddy proxy: uvicorn's --proxy-headers --forwarded-allow-ips='*'
# wraps the app in ProxyHeadersMiddleware, exercised here without a server.

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.auth.security import hash_password
from app.core.config import get_settings
from app.db.base import get_db
from app.main import app
from app.models import User

PASSWORD = "correct-horse-battery"
LAN_HOST = "192.168.1.50"


@pytest.fixture(name="proxied")
def proxied_fixture(db_factory: sessionmaker) -> Iterator[TestClient]:
    with db_factory() as db:
        db.add(
            User(username="owner", password_hash=hash_password(PASSWORD), role="owner")
        )
        db.commit()

    def override_get_db():
        db = db_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    wrapped = ProxyHeadersMiddleware(app, trusted_hosts="*")
    with TestClient(wrapped, base_url=f"http://{LAN_HOST}") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


def _login(client: TestClient, username: str, password: str, headers: dict):
    return client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
        headers=headers,
    )


def test_forwarded_https_origin_passes_the_origin_guard(proxied: TestClient) -> None:
    response = _login(
        proxied,
        "owner",
        PASSWORD,
        {
            "Host": LAN_HOST,
            "X-Forwarded-Proto": "https",
            "Origin": f"https://{LAN_HOST}",
        },
    )
    assert response.status_code == 200


def test_https_origin_without_forwarded_proto_is_rejected(
    proxied: TestClient,
) -> None:
    response = _login(
        proxied,
        "owner",
        PASSWORD,
        {"Host": LAN_HOST, "Origin": f"https://{LAN_HOST}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Cross-origin request rejected"


def test_address_throttle_keys_on_forwarded_for(
    proxied: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    limit = 3
    monkeypatch.setattr(get_settings(), "login_max_failures_per_address", limit)
    first = {"X-Forwarded-For": "192.168.1.60"}
    second = {"X-Forwarded-For": "192.168.1.61"}

    # Distinct usernames keep the per-account limit out of the way.
    for index in range(limit):
        assert (
            _login(proxied, f"guess{index}", "wrong-password-123", first).status_code
            == 401
        )
    assert _login(proxied, "owner", PASSWORD, first).status_code == 429
    assert _login(proxied, "owner", PASSWORD, second).status_code == 200
