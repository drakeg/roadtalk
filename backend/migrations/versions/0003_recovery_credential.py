"""Add privacy-preserving anonymous recovery credentials.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recovery_credential",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("key_id", sa.Uuid(), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("rotated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_recovery_credential_account_id_account",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("account_id", name="pk_recovery_credential"),
        sa.UniqueConstraint("key_id", name="uq_recovery_credential_key_id"),
    )


def downgrade() -> None:
    op.drop_table("recovery_credential")
