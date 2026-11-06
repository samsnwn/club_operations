"""Administrator-managed account API tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth.security import hash_password
from app.auth.sessions import create_session
from app.models import AuthSession, User

PASSWORD = "correct horse battery"


def _add_user(
    factory: sessionmaker,
    username: str,
    role: str,
    *,
    password: str = PASSWORD,
    must_change_password: bool = False,
) -> int:
    with factory() as db:
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            must_change_password=must_change_password,
        )
        db.add(user)
        db.commit()
        return user.id


def _login(client: TestClient, username: str, password: str = PASSWORD) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text


@pytest.fixture(name="admin")
def admin_fixture(api_client: TestClient, db_factory: sessionmaker) -> TestClient:
    _add_user(db_factory, "admin", "admin")
    _login(api_client, "admin")
    return api_client


@pytest.fixture(name="owner")
def owner_fixture(api_client: TestClient, db_factory: sessionmaker) -> TestClient:
    _add_user(db_factory, "owner", "owner")
    _login(api_client, "owner")
    return api_client


def test_staff_cannot_list_users(
    api_client: TestClient, db_factory: sessionmaker
) -> None:
    _add_user(db_factory, "staff", "staff")
    _login(api_client, "staff")

    assert api_client.get("/api/v1/users").status_code == 403


def test_owner_lists_and_creates_staff(
    owner: TestClient, db_factory: sessionmaker
) -> None:
    response = owner.post(
        "/api/v1/users",
        json={
            "username": "newstaff",
            "password": "temporary-password",
            "role": "staff",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "newstaff"
    assert body["role"] == "staff"
    assert body["created_by"] == "owner"
    assert body["must_change_password"] is True
    assert "password_hash" not in body

    listing = owner.get("/api/v1/users").json()
    assert {user["username"] for user in listing} == {"owner", "newstaff"}


def test_admin_creates_staff_only(admin: TestClient, db_factory: sessionmaker) -> None:
    created = admin.post(
        "/api/v1/users",
        json={
            "username": "newstaff",
            "password": "temporary-password",
            "role": "staff",
        },
    )
    escalated = admin.post(
        "/api/v1/users",
        json={"username": "peer", "password": "temporary-password", "role": "admin"},
    )

    assert created.status_code == 201
    assert created.json()["created_by"] == "admin"
    assert escalated.status_code == 403


def test_owner_creates_privileged_accounts(
    owner: TestClient, db_factory: sessionmaker
) -> None:
    for role in ("admin", "owner"):
        response = owner.post(
            "/api/v1/users",
            json={
                "username": f"new-{role}",
                "password": "temporary-password",
                "role": role,
            },
        )
        assert response.status_code == 201
        assert response.json()["role"] == role


def test_duplicate_username_conflicts(
    owner: TestClient, db_factory: sessionmaker
) -> None:
    payload = {
        "username": "duplicate",
        "password": "temporary-password",
        "role": "staff",
    }
    assert owner.post("/api/v1/users", json=payload).status_code == 201
    assert owner.post("/api/v1/users", json=payload).status_code == 409


def test_weak_or_invalid_creation_payload_is_rejected(owner: TestClient) -> None:
    short_password = owner.post(
        "/api/v1/users", json={"username": "staff", "password": "short"}
    )
    bad_username = owner.post(
        "/api/v1/users",
        json={"username": "bad name!", "password": "temporary-password"},
    )
    assert short_password.status_code == 422
    assert bad_username.status_code == 422


def test_admin_cannot_manage_privileged_accounts(
    admin: TestClient, db_factory: sessionmaker
) -> None:
    target_id = _add_user(db_factory, "other-admin", "admin")

    patch = admin.patch(f"/api/v1/users/{target_id}", json={"is_active": False})
    reset = admin.post(
        f"/api/v1/users/{target_id}/reset-password",
        json={"new_password": "temporary-password"},
    )

    assert patch.status_code == 403
    assert reset.status_code == 403


def test_owner_deactivates_staff_and_revokes_sessions(
    owner: TestClient, db_factory: sessionmaker
) -> None:
    staff_id = _add_user(db_factory, "staff", "staff")
    with db_factory() as db:
        create_session(db, staff_id, ttl_hours=12)

    response = owner.patch(f"/api/v1/users/{staff_id}", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    with db_factory() as db:
        assert (
            db.query(AuthSession).filter(AuthSession.user_id == staff_id).count() == 0
        )


def test_owner_cannot_change_own_account(
    owner: TestClient, db_factory: sessionmaker
) -> None:
    with db_factory() as db:
        own_id = db.query(User).filter(User.username == "owner").one().id

    assert (
        owner.patch(f"/api/v1/users/{own_id}", json={"is_active": False}).status_code
        == 409
    )
    assert (
        owner.post(
            f"/api/v1/users/{own_id}/reset-password",
            json={"new_password": "temporary-password"},
        ).status_code
        == 403
    )


def test_reset_password_forces_change_and_revokes_sessions(
    owner: TestClient, db_factory: sessionmaker
) -> None:
    staff_id = _add_user(db_factory, "staff", "staff")

    response = owner.post(
        f"/api/v1/users/{staff_id}/reset-password",
        json={"new_password": "replacement-password"},
    )

    assert response.status_code == 200
    with db_factory() as db:
        user = db.get(User, staff_id)
        assert user.must_change_password is True
        assert (
            db.query(AuthSession).filter(AuthSession.user_id == staff_id).count() == 0
        )

    # Old password no longer works; the temporary one does and is gated.
    old_login = owner.post(
        "/api/v1/auth/login", json={"username": "staff", "password": PASSWORD}
    )
    new_login = owner.post(
        "/api/v1/auth/login",
        json={"username": "staff", "password": "replacement-password"},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200
    assert new_login.json()["must_change_password"] is True


def test_staff_cannot_modify_or_reset(
    api_client: TestClient, db_factory: sessionmaker
) -> None:
    _add_user(db_factory, "staff", "staff")
    target_id = _add_user(db_factory, "target", "staff")
    _login(api_client, "staff")

    assert (
        api_client.patch(
            f"/api/v1/users/{target_id}", json={"is_active": False}
        ).status_code
        == 403
    )
    assert (
        api_client.post(
            f"/api/v1/users/{target_id}/reset-password",
            json={"new_password": "temporary-password"},
        ).status_code
        == 403
    )


def test_unknown_user_is_404(owner: TestClient) -> None:
    assert (
        owner.patch("/api/v1/users/9999", json={"is_active": False}).status_code == 404
    )
    assert (
        owner.post(
            "/api/v1/users/9999/reset-password",
            json={"new_password": "temporary-password"},
        ).status_code
        == 404
    )
