# Failed sign-in throttling: per-account and per-address limits on /auth/login.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth import routes
from app.auth.security import hash_password
from app.auth.throttle import FailureThrottle
from app.core.config import get_settings
from app.models import User

PASSWORD = "correct-horse-battery"


@pytest.fixture(name="client")
def client_fixture(api_client: TestClient, db_factory: sessionmaker) -> TestClient:
    with db_factory() as db:
        db.add(
            User(username="owner", password_hash=hash_password(PASSWORD), role="owner")
        )
        db.commit()
    return api_client


def _login(client: TestClient, username: str, password: str):
    return client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )


def test_account_is_blocked_after_too_many_failures(client: TestClient) -> None:
    limit = get_settings().login_max_failures_per_account
    for _ in range(limit):
        assert _login(client, "owner", "wrong-password-123").status_code == 401

    # Even the correct password is refused while the account is throttled.
    response = _login(client, "owner", PASSWORD)
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0


def test_blocked_attempt_is_not_hashed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    for _ in range(get_settings().login_max_failures_per_account):
        _login(client, "owner", "wrong-password-123")

    def no_hash(*_args: object) -> bool:
        raise AssertionError("a throttled attempt must not reach Argon2")

    monkeypatch.setattr(routes, "verify_password", no_hash)
    assert _login(client, "owner", PASSWORD).status_code == 429


def test_username_case_does_not_evade_the_account_limit(client: TestClient) -> None:
    for index in range(get_settings().login_max_failures_per_account):
        name = "owner" if index % 2 else "OWNER"
        _login(client, name, "wrong-password-123")
    assert _login(client, "Owner", "wrong-password-123").status_code == 429


def test_address_is_blocked_across_many_usernames(client: TestClient) -> None:
    limit = get_settings().login_max_failures_per_address
    for index in range(limit):
        assert _login(client, f"guess{index}", "wrong-password-123").status_code == 401
    # A different, valid account from the same address is refused too.
    assert _login(client, "owner", PASSWORD).status_code == 429


def test_successful_login_clears_the_account_counter(client: TestClient) -> None:
    limit = get_settings().login_max_failures_per_account
    for _ in range(limit - 1):
        _login(client, "owner", "wrong-password-123")
    assert _login(client, "owner", PASSWORD).status_code == 200
    for _ in range(limit - 1):
        assert _login(client, "owner", "wrong-password-123").status_code == 401
    assert _login(client, "owner", PASSWORD).status_code == 200


def test_oversized_password_is_rejected_before_hashing(client: TestClient) -> None:
    assert _login(client, "owner", "x" * 5000).status_code == 422


def test_failures_age_out_of_the_window(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = {"now": 1000.0}
    monkeypatch.setattr("app.auth.throttle.time.monotonic", lambda: clock["now"])
    throttle = FailureThrottle()
    for _ in range(3):
        throttle.record_failure("key", 60.0)
    assert throttle.retry_after("key", 3, 60.0) == 60
    clock["now"] += 59.0
    assert throttle.retry_after("key", 3, 60.0) == 1
    clock["now"] += 1.0
    assert throttle.retry_after("key", 3, 60.0) == 0
