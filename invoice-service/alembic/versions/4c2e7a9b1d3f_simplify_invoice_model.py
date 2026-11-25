"""simplify invoice model: suggestions, exact money, no watermarks

Drops the unused sync watermarks and the never-populated columns (confidence,
currency, category/payment_method/description guesses), renames `*_guess` to
`*_suggested`, and stores money as exact decimals. Existing rows survive.

Revision ID: 4c2e7a9b1d3f
Revises: 8d9f3c1a2b4e
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4c2e7a9b1d3f"
down_revision: str | None = "8d9f3c1a2b4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEXT_FIELDS = ("supplier", "invoice_number", "invoice_date", "due_date")
AMOUNT_FIELDS = ("net", "vat", "gross")
# Frozen copy of app.models.invoice.REQUIRED_FIELDS at this revision.
REQUIRED_FIELDS = ("supplier", "invoice_date", "gross")
UNSUGGESTED_FIELDS = (
    ("category", sa.String(length=64)),
    ("payment_method", sa.String(length=64)),
    ("description", sa.Text()),
)
MONEY = sa.Numeric(12, 2)


def upgrade() -> None:
    op.drop_table("sync_watermarks")
    with op.batch_alter_table("invoices") as batch:
        batch.drop_column("confidence")
        batch.drop_column("currency")
        for name, _ in UNSUGGESTED_FIELDS:
            batch.drop_column(f"{name}_guess")
        for name in TEXT_FIELDS:
            batch.alter_column(f"{name}_guess", new_column_name=f"{name}_suggested")
        for name in AMOUNT_FIELDS:
            batch.alter_column(
                f"{name}_guess",
                new_column_name=f"{name}_suggested",
                type_=MONEY,
                existing_type=sa.Float(),
            )
            batch.alter_column(f"{name}_final", type_=MONEY, existing_type=sa.Float())
    # Open rows were triaged by the dropped confidence score; re-triage them by
    # the new rule (a required suggestion is missing → needs_attention).
    # Reviewed rows (confirmed/rejected) keep their status.
    missing_required = " OR ".join(
        f"{name}_suggested IS NULL" for name in REQUIRED_FIELDS
    )
    op.execute(
        "UPDATE invoices SET status = CASE WHEN "
        f"{missing_required} THEN 'needs_attention' ELSE 'pending_review' END "
        "WHERE status IN ('needs_attention', 'pending_review')"
    )

#test comment
def downgrade() -> None:
    with op.batch_alter_table("invoices") as batch:
        for name in AMOUNT_FIELDS:
            batch.alter_column(f"{name}_final", type_=sa.Float(), existing_type=MONEY)
            batch.alter_column(
                f"{name}_suggested",
                new_column_name=f"{name}_guess",
                type_=sa.Float(),
                existing_type=MONEY,
            )
        for name in TEXT_FIELDS:
            batch.alter_column(f"{name}_suggested", new_column_name=f"{name}_guess")
        for name, column_type in UNSUGGESTED_FIELDS:
            batch.add_column(sa.Column(f"{name}_guess", column_type, nullable=True))
        batch.add_column(sa.Column("currency", sa.String(length=8), nullable=True))
        batch.add_column(
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0")
        )
    op.create_table(
        "sync_watermarks",
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("cursor", sa.Text(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("source"),
    )
