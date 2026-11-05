"""baseline — invoices, sync watermarks

Revision ID: bcd6daea9721
Revises:
Create Date: 2026-11-05 13:35:46.564433
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "bcd6daea9721"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
