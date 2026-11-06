"""Management commands for bootstrapping and recovering accounts.

Staff accounts are created by an administrator in the app. This CLI exists for
the two cases the app cannot cover: the first owner (nothing exists yet) and
recovery when nobody can log in.

Usage:

    uv run python -m app.cli create-user --username owner --role owner
    uv run python -m app.cli reset-password --username owner

The password is read from `NEW_USER_PASSWORD` when set (Docker/CI), otherwise
prompted for twice without echo.
"""

import argparse
import getpass
import os
import sys

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.auth.accounts import ROLES, validate_password, validate_username
from app.auth.security import hash_password
from app.db.base import SessionLocal
from app.models import AuthSession, User


def _read_password() -> str:
    password = os.environ.get("NEW_USER_PASSWORD")
    if password is None:
        password = getpass.getpass("Password: ")
        confirmation = getpass.getpass("Repeat password: ")
        if password != confirmation:
            raise SystemExit("Passwords do not match")
    try:
        return validate_password(password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def _username(value: str) -> str:
    try:
        return validate_username(value)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def create_user(args: argparse.Namespace) -> int:
    username = _username(args.username)
    password = _read_password()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == username)) is not None:
            raise SystemExit(f"User {username!r} already exists")
        db.add(
            User(
                username=username,
                password_hash=hash_password(password),
                role=args.role,
                created_by=None,
            )
        )
        db.commit()
    print(f"Created {args.role} account {username!r}")
    return 0


def reset_password(args: argparse.Namespace) -> int:
    username = _username(args.username)
    password = _read_password()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            raise SystemExit(f"User {username!r} does not exist")
        user.password_hash = hash_password(password)
        user.must_change_password = True
        # Recovery must revoke every existing session for that account.
        db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
        db.commit()
    print(f"Reset password for {username!r}; they must choose a new one at login")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Bootstrap and recover internal accounts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-user", help="Create an account")
    create.add_argument("--username", required=True)
    create.add_argument("--role", choices=ROLES, default="staff")
    create.set_defaults(func=create_user)

    reset = subparsers.add_parser("reset-password", help="Reset a password")
    reset.add_argument("--username", required=True)
    reset.set_defaults(func=reset_password)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except OperationalError as exc:
        raise SystemExit(
            "Database not initialised — run `uv run alembic upgrade head`"
        ) from exc


if __name__ == "__main__":
    sys.exit(main())
