"""Add bounded notification delivery idempotency receipts.

Revision ID: 0016
Revises: 0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_delivery_receipt",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key_hash", sa.String(64), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("notification_id", sa.Uuid(), nullable=True),
        sa.Column("guard_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "length(idempotency_key_hash) = 64",
            name="ck_notification_delivery_receipt_idempotency_hash_valid",
        ),
        sa.CheckConstraint(
            "length(request_fingerprint) = 64",
            name="ck_notification_delivery_receipt_request_fingerprint_valid",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_notification_delivery_receipt_account_id_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["notification_id"],
            ["notification.id"],
            name="fk_notification_delivery_receipt_notification_id_notification",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "account_id",
            "idempotency_key_hash",
            name="pk_notification_delivery_receipt",
        ),
    )
    op.create_index(
        "ix_notification_delivery_receipt_guard_expires",
        "notification_delivery_receipt",
        ["guard_expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_delivery_receipt_guard_expires",
        table_name="notification_delivery_receipt",
    )
    op.drop_table("notification_delivery_receipt")
