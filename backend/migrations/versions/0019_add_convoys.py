"""Add Sprint 11 convoy persistence.

Revision ID: 0019
Revises: 0018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "convoy",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("leader_account_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), server_default="active", nullable=False),
        sa.Column("disbanded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("state IN ('active', 'disbanded')", name="ck_convoy_state_allowed"),
        sa.CheckConstraint("length(display_name) > 0", name="ck_convoy_display_name_present"),
        sa.CheckConstraint("version >= 1", name="ck_convoy_version_positive"),
        sa.ForeignKeyConstraint(["leader_account_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_convoy_leader_state", "convoy", ["leader_account_id", "state"])

    op.create_table(
        "convoy_membership",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("convoy_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("state", sa.String(16), server_default="active", nullable=False),
        sa.Column(\n            "joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False\n        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "role IN ('leader', 'member')", name="ck_convoy_membership_role_allowed"
        ),
        sa.CheckConstraint(
            "state IN ('active', 'left', 'revoked', 'expired')",
            name="ck_convoy_membership_state_allowed",
        ),
        sa.CheckConstraint(
            "(state = 'active' AND ended_at IS NULL) OR "
            "(state <> 'active' AND ended_at IS NOT NULL)",
            name="ck_convoy_membership_state_timestamp_consistent",
        ),
        sa.CheckConstraint("version >= 1", name="ck_convoy_membership_version_positive"),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["convoy_id"], ["convoy.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_convoy_membership_convoy_account",
        "convoy_membership",
        ["convoy_id", "account_id"],
        unique=True,
    )
    op.create_index(
        "ix_convoy_membership_account_state", "convoy_membership", ["account_id", "state"]
    )
    op.create_index(
        "ix_convoy_membership_convoy_state", "convoy_membership", ["convoy_id", "state"]
    )


def downgrade() -> None:
    op.drop_index("ix_convoy_membership_convoy_state", table_name="convoy_membership")
    op.drop_index("ix_convoy_membership_account_state", table_name="convoy_membership")
    op.drop_index("uq_convoy_membership_convoy_account", table_name="convoy_membership")
    op.drop_table("convoy_membership")
    op.drop_index("ix_convoy_leader_state", table_name="convoy")
    op.drop_table("convoy")
