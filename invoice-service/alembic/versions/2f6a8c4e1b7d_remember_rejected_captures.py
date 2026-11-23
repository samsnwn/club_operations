"""remember rejected captures: skip files that will always be rejected

Files over the PDF page limit are recorded by MD5 so the invoice folder stops
downloading them on every import.

Revision ID: 2f6a8c4e1b7d
Revises: 7e1b3d5f9a2c
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2f6a8c4e1b7d"
down_revision: str | None = "7e1b3d5f9a2c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rejected_captures",
        sa.Column("content_md5", sa.String(length=32), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("rejected_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("content_md5"),
    )


def downgrade() -> None:
    op.drop_table("rejected_captures")
