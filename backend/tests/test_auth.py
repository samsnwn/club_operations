"""Authentication API tests: login, sessions, password gate, origin guard."""

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth.dependencies import current_user
from app.auth.security import hash_password
from app.auth.sessions import create_session, hash_token
from app.models import AuthSession, User

PASSWORD = "correct horse battery"


@pytest.fixture(name="auth")
def auth_fixture(
    api_client: TestClient, db_factory: sessionmaker
) -> tuple[TestClient, sessionmaker]:
    """Keep the `(client, session factory)` shape used by these tests."""
    return api_client, db_factory


def _add_user(
    factory: sessionmaker,
    *,
    username: str = "owner",
    password: str = PASSWORD,
    role: str = "owner",
    is_active: bool = True,
    must_change_password: bool = False,
) -> int:
    with factory() as db:
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
            must_change_password=must_change_password,
        )
        db.add(user)
        db.commit()
        return user.id


def _login(client: TestClient, username: str = "owner", password: str = PASSWORD):
    return client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )


def test_login_sets_http_only_cookie_and_me(auth) -> None:
    client, factory = auth
    _add_user(factory)

    response = _login(client)

    assert response.status_code == 200
    assert response.json() == {
        "username": "owner",
        "role": "owner",
        "must_change_password": False,
    }
    cookie = response.headers["set-cookie"].lower()
    assert "bv_session=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert client.get("/api/v1/auth/me").json()["username"] == "owner"


@pytest.mark.parametrize("password", ["wrong password", "correct horse batterY"])
def test_login_rejects_wrong_password(auth, password: str) -> None:
    client, factory = auth
    _add_user(factory)

    response = _login(client, password=password)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_rejects_unknown_user(auth) -> None:
    client, _factory = auth
    response = _login(client, username="nobody")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_rejects_inactive_account(auth) -> None:
    client, factory = auth
    _add_user(factory, is_active=False)
    assert _login(client).status_code == 401


def test_protected_route_requires_login(auth) -> None:
    client, _factory = auth
    response = client.get("/api/v1/invoices/queue")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_password_change_required_blocks_api(auth) -> None:
    client, factory = auth
    _add_user(factory, must_change_password=True)

    assert _login(client).status_code == 200
    response = client.get("/api/v1/invoices/queue")

    assert response.status_code == 403
    assert response.json()["detail"] == "Password change required"


def test_password_change_clears_gate(auth) -> None:
    client, factory = auth
    _add_user(factory, must_change_password=True)
    _login(client)

    response = client.post(
        "/api/v1/auth/password",
        json={"current_password": PASSWORD, "new_password": "a brand new passphrase"},
    )

    assert response.status_code == 200
    me = client.get("/api/v1/auth/me").json()
    assert me["must_change_password"] is False
    assert client.get("/api/v1/invoices/queue").status_code != 403


def test_password_change_rejects_wrong_current_password(auth) -> None:
    client, factory = auth
    _add_user(factory)
    _login(client)

    response = client.post(
        "/api/v1/auth/password",
        json={
            "current_password": "not the password",
            "new_password": "another passphrase",
        },
    )
    assert response.status_code == 400


def test_password_change_rejects_short_or_repeated_password(auth) -> None:
    client, factory = auth
    _add_user(factory)
    _login(client)

    too_short = client.post(
        "/api/v1/auth/password",
        json={"current_password": PASSWORD, "new_password": "short"},
    )
    repeated = client.post(
        "/api/v1/auth/password",
        json={"current_password": PASSWORD, "new_password": PASSWORD},
    )

    assert too_short.status_code == 400
    assert repeated.status_code == 400


def test_password_change_revokes_other_sessions(auth) -> None:
    client, factory = auth
    user_id = _add_user(factory)
    _login(client)

    with factory() as db:
        other_token = create_session(db, user_id, ttl_hours=12)
        other_hash = hash_token(other_token)

    assert (
        client.post(
            "/api/v1/auth/password",
            json={"current_password": PASSWORD, "new_password": "another passphrase"},
        ).status_code
        == 200
    )

    with factory() as db:
        remaining = db.query(AuthSession).filter(AuthSession.user_id == user_id).all()
        assert len(remaining) == 1
        assert remaining[0].token_hash != other_hash
    # The browser that changed the password keeps working with its new cookie.
    assert client.get("/api/v1/auth/me").status_code == 200


def test_logout_revokes_session(auth) -> None:
    client, factory = auth
    _add_user(factory)
    _login(client)

    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_inactive_account_session_is_rejected(auth) -> None:
    client, factory = auth
    user_id = _add_user(factory)
    _login(client)

    with factory() as db:
        user = db.get(User, user_id)
        user.is_active = False
        db.commit()

    assert client.get("/api/v1/auth/me").status_code == 401


def test_expired_session_is_rejected(auth) -> None:
    client, factory = auth
    user_id = _add_user(factory)
    with factory() as db:
        token = create_session(db, user_id, ttl_hours=12)
        session = db.query(AuthSession).one()
        session.expires_at = datetime.now() - timedelta(minutes=1)
        db.commit()

    client.cookies.set("bv_session", token)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_cross_origin_state_change_is_rejected(auth) -> None:
    client, factory = auth
    _add_user(factory)

    rejected = client.post(
        "/api/v1/auth/login",
        json={"username": "owner", "password": PASSWORD},
        headers={"Origin": "http://evil.example"},
    )
    allowed = client.post(
        "/api/v1/auth/login",
        json={"username": "owner", "password": PASSWORD},
        headers={"Origin": "http://localhost:5173"},
    )

    assert rejected.status_code == 403
    assert rejected.json()["detail"] == "Cross-origin request rejected"
    assert allowed.status_code == 200


def test_current_user_blocks_password_change_flag() -> None:
    user = User(
        id=1,
        username="staff",
        password_hash="unused",
        role="staff",
        is_active=True,
        must_change_password=True,
    )
    with pytest.raises(HTTPException) as exc:
        current_user(user)
    assert exc.value.status_code == 403

    user.must_change_password = False
    assert current_user(user) is user
