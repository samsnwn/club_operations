"""track invoice-folder originals: content MD5 and source reference

`content_md5` lets the invoice folder skip known files before downloading
them (Drive reports MD5 checksums); existing rows learn it the first time
their file is captured again. `source_ref` holds the Drive file ID.

Revision ID: 7e1b3d5f9a2c
Revises: 4c2e7a9b1d3f
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7e1b3d5f9a2c"
down_revision: str | None = "4c2e7a9b1d3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("invoices") as batch:
        batch.add_column(sa.Column("content_md5", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("source_ref", sa.String(length=128), nullable=True))
        batch.create_index("ix_invoices_content_md5", ["content_md5"])


def downgrade() -> None:
    with op.batch_alter_table("invoices") as batch:
        batch.drop_index("ix_invoices_content_md5")
        batch.drop_column("source_ref")
        batch.drop_column("content_md5")
