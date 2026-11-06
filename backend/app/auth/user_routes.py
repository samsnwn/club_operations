"""Administrator-managed accounts.

There is no self-registration: owners manage every account, admins manage
staff accounts only. Administrator-provisioned passwords are temporary and
must be replaced at first login.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.accounts import MIN_PASSWORD_LENGTH, USERNAME_PATTERN, Role
from app.auth.dependencies import require_role
from app.auth.security import hash_password
from app.auth.sessions import delete_user_sessions
from app.db.base import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])

Manager = Annotated[User, Depends(require_role("owner", "admin"))]


class CreateUserPayload(BaseModel):
    username: str = Field(min_length=1, max_length=32, pattern=USERNAME_PATTERN.pattern)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    role: Role = "staff"


class UpdateUserPayload(BaseModel):
    role: Role | None = None
    is_active: bool | None = None


class ResetPasswordPayload(BaseModel):
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH)


def _public(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "must_change_password": user.must_change_password,
        "created_by": user.created_by,
    }


def _check_can_manage(actor: User, target: User) -> None:
    if actor.role != "owner" and target.role != "staff":
        raise HTTPException(
            status_code=403, detail="Admins can only manage staff accounts"
        )


@router.get("")
def list_users(
    _actor: Manager,
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    users = db.query(User).order_by(User.username).all()
    return [_public(user) for user in users]


@router.post("", status_code=201)
def create_user(
    payload: CreateUserPayload,
    actor: Manager,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if actor.role != "owner" and payload.role != "staff":
        raise HTTPException(
            status_code=403, detail="Admins can only create staff accounts"
        )

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        must_change_password=True,
        created_by=actor.username,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists") from exc
    db.refresh(user)
    return _public(user)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    payload: UpdateUserPayload,
    actor: Manager,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_can_manage(actor, target)

    if target.id == actor.id:
        raise HTTPException(
            status_code=409, detail="You cannot change your own role or status"
        )
    if payload.role is not None and actor.role != "owner" and payload.role != "staff":
        raise HTTPException(
            status_code=403, detail="Admins can only manage staff accounts"
        )

    losing_owner = (
        target.role == "owner"
        and target.is_active
        and (
            (payload.role is not None and payload.role != "owner")
            or payload.is_active is False
        )
    )
    if losing_owner:
        active_owners = (
            db.query(User)
            .filter(User.role == "owner", User.is_active.is_(True))
            .count()
        )
        if active_owners <= 1:
            raise HTTPException(
                status_code=409, detail="At least one active owner is required"
            )

    role_changed = payload.role is not None and payload.role != target.role
    deactivated = payload.is_active is False and target.is_active
    if payload.role is not None:
        target.role = payload.role
    if payload.is_active is not None:
        target.is_active = payload.is_active
    db.commit()
    db.refresh(target)

    if role_changed or deactivated:
        delete_user_sessions(db, target.id)
    return _public(target)


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: ResetPasswordPayload,
    actor: Manager,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_can_manage(actor, target)

    if target.id == actor.id:
        raise HTTPException(
            status_code=403,
            detail="Use /auth/password to change your own password",
        )

    target.password_hash = hash_password(payload.new_password)
    target.must_change_password = True
    db.commit()
    delete_user_sessions(db, target.id)
    return {"id": target.id, "status": "password_reset"}
