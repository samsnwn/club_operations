"""Login, logout, identity and password-change endpoints.

Accounts are never self-registered: administrators create them (step 4), and
the CLI bootstraps the first owner. This module only authenticates existing
accounts.
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.accounts import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.auth.dependencies import authenticated_user
from app.auth.security import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.auth.sessions import (
    COOKIE_NAME,
    create_session,
    delete_session,
    delete_user_sessions,
)
from app.auth.throttle import login_throttle
from app.core.config import get_settings
from app.db.base import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)


class PasswordPayload(BaseModel):
    current_password: str = Field(max_length=MAX_PASSWORD_LENGTH)
    new_password: str = Field(max_length=MAX_PASSWORD_LENGTH)


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


def _identity(user: User) -> dict:
    return {
        "username": user.username,
        "role": user.role,
        "must_change_password": user.must_change_password,
    }


@router.post("/login")
def login(
    payload: LoginPayload,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    settings = get_settings()
    window = settings.login_failure_window_minutes * 60.0
    address = request.client.host if request.client else "unknown"
    account_key = f"account:{payload.username.lower()}"
    address_key = f"address:{address}"
    # Checked before any hashing, and identically for unknown usernames, so a
    # refusal neither costs an Argon2 run nor reveals whether the account exists.
    retry_after = max(
        login_throttle.retry_after(
            account_key, settings.login_max_failures_per_account, window
        ),
        login_throttle.retry_after(
            address_key, settings.login_max_failures_per_address, window
        ),
    )
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Too many failed sign-in attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = db.scalar(select(User).where(User.username == payload.username))
    # Always hash-compare so a missing username and a wrong password take the
    # same time (no account enumeration through timing).
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_ok = verify_password(payload.password, password_hash)
    if user is None or not user.is_active or not password_ok:
        login_throttle.record_failure(account_key, window)
        login_throttle.record_failure(address_key, window)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    login_throttle.reset(account_key)
    token = create_session(db, user.id, settings.session_ttl_hours)
    _set_session_cookie(response, token)
    return _identity(user)


@router.post("/logout")
def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> dict:
    if session_token:
        delete_session(db, session_token)
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "logged_out"}


@router.get("/me")
def me(user: Annotated[User, Depends(authenticated_user)]) -> dict:
    return _identity(user)


@router.post("/password")
def change_password(
    payload: PasswordPayload,
    response: Response,
    user: Annotated[User, Depends(authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
        )
    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=400, detail="New password must differ from the current one"
        )

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()

    # Revoke every existing session, then issue a fresh one for this browser.
    delete_user_sessions(db, user.id)
    token = create_session(db, user.id, get_settings().session_ttl_hours)
    _set_session_cookie(response, token)
    return {"status": "password_changed"}
