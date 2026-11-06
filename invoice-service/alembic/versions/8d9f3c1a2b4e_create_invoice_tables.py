"""create invoice and sync watermark tables

Revision ID: 8d9f3c1a2b4e
Revises: bcd6daea9721
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8d9f3c1a2b4e"
down_revision: str | None = "bcd6daea9721"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sync_watermarks",
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("cursor", sa.Text(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("source"),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("supplier_guess", sa.String(length=255), nullable=True),
        sa.Column("invoice_number_guess", sa.String(length=64), nullable=True),
        sa.Column("invoice_date_guess", sa.String(length=32), nullable=True),
        sa.Column("due_date_guess", sa.String(length=32), nullable=True),
        sa.Column("net_guess", sa.Float(), nullable=True),
        sa.Column("vat_guess", sa.Float(), nullable=True),
        sa.Column("gross_guess", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("category_guess", sa.String(length=64), nullable=True),
        sa.Column("payment_method_guess", sa.String(length=64), nullable=True),
        sa.Column("description_guess", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("supplier_final", sa.String(length=255), nullable=True),
        sa.Column("invoice_number_final", sa.String(length=64), nullable=True),
        sa.Column("invoice_date_final", sa.String(length=32), nullable=True),
        sa.Column("due_date_final", sa.String(length=32), nullable=True),
        sa.Column("net_final", sa.Float(), nullable=True),
        sa.Column("vat_final", sa.Float(), nullable=True),
        sa.Column("gross_final", sa.Float(), nullable=True),
        sa.Column("category_final", sa.String(length=64), nullable=True),
        sa.Column("payment_method_final", sa.String(length=64), nullable=True),
        sa.Column("description_final", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=64), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("exported_at", sa.DateTime(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash", name="uq_invoice_content_hash"),
    )


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_table("sync_watermarks")
