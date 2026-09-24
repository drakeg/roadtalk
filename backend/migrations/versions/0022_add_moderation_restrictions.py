"""Add Sprint 12 mute/block restrictions.

Revision ID: 0022
Revises: 0021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "moderation_restriction",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_account_id", sa.Uuid(), nullable=False),
        sa.Column("subject_account_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("state", sa.String(16), server_default="active", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("kind IN ('mute', 'block')", name="ck_moderation_restriction_kind_allowed"),
        sa.CheckConstraint(
            "state IN ('active', 'revoked', 'expired')",
            name="ck_moderation_restriction_state_allowed",
        ),
        sa.CheckConstraint(
            "actor_account_id <> subject_account_id",
            name="ck_moderation_restriction_different_accounts",
        ),
        sa.CheckConstraint(
            "(state = 'active' AND ended_at IS NULL) OR "
            "(state <> 'active' AND ended_at IS NOT NULL)",
            name="ck_moderation_restriction_state_timestamp_consistent",
        ),
        sa.CheckConstraint("version >= 1", name="ck_moderation_restriction_version_positive"),
        sa.ForeignKeyConstraint(["actor_account_id"], ["account.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_account_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_moderation_restriction_active_pair_kind",
        "moderation_restriction",
        ["actor_account_id", "subject_account_id", "kind"],
        unique=True,
        postgresql_where=sa.text("state = 'active'"),
    )
    op.create_index(
        "ix_moderation_restriction_subject_state",
        "moderation_restriction",
        ["subject_account_id", "state"],
    )


def downgrade() -> None:
    op.drop_index("ix_moderation_restriction_subject_state", table_name="moderation_restriction")
    op.drop_index(
        "uq_moderation_restriction_active_pair_kind",
        table_name="moderation_restriction",
    )
    op.drop_table("moderation_restriction")
