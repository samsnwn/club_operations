"""Account validation rules shared by the CLI and the user-management API."""

import re
from typing import Literal

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,32}$")
MIN_PASSWORD_LENGTH = 12
ROLES = ("owner", "admin", "staff")
Role = Literal["owner", "admin", "staff"]


def validate_username(value: str) -> str:
    if not USERNAME_PATTERN.fullmatch(value):
        raise ValueError(
            "Username must be 1-32 characters: letters, digits, dot, underscore "
            "or hyphen"
        )
    return value


def validate_password(value: str) -> str:
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    return value
