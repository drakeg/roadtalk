"""Add the optional account identity profile.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profile",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("normalized_callsign", sa.String(32), nullable=True),
        sa.Column("display_callsign", sa.String(32), nullable=True),
        sa.Column("avatar_id", sa.String(64), nullable=True),
        sa.Column(
            "setup_completed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("callsign_changed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "(normalized_callsign IS NULL AND display_callsign IS NULL) OR "
            "(normalized_callsign IS NOT NULL AND display_callsign IS NOT NULL)",
            name="ck_profile_callsign_pair",
        ),
        sa.CheckConstraint(
            "NOT setup_completed OR "
            "(normalized_callsign IS NOT NULL AND display_callsign IS NOT NULL "
            "AND avatar_id IS NOT NULL)",
            name="ck_profile_completed_fields",
        ),
        sa.CheckConstraint("version >= 1", name="ck_profile_version_positive"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_profile_account_id_account",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("account_id", name="pk_profile"),
    )
    op.create_index(
        "uq_profile_normalized_callsign",
        "profile",
        ["normalized_callsign"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("profile")
