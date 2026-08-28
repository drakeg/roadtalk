"""Add registered account credentials.

Revision ID: 0014
Revises: 0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "registered_credential",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("normalized_username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_index(
        "uq_registered_credential_username",
        "registered_credential",
        ["normalized_username"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_registered_credential_username",
        table_name="registered_credential",
    )
    op.drop_table("registered_credential")
