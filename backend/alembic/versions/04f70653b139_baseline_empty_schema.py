"""baseline — empty schema

Revision ID: 04f70653b139
Revises: 
Create Date: 2026-11-05 00:25:47.007468
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op



revision: str = '04f70653b139'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
