"""Add Sprint 12 moderation report persistence.

Revision ID: 0021
Revises: 0020
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "moderation_report",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reporter_account_id", sa.Uuid(), nullable=False),
        sa.Column("subject_account_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("state", sa.String(16), server_default="submitted", nullable=False),
        sa.Column("idempotency_key_hash", sa.String(64), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "reason IN ('harassment', 'spam', 'impersonation', 'unsafe_content', 'other')",
            name="ck_moderation_report_reason_allowed",
        ),
        sa.CheckConstraint(
            "state IN ('submitted', 'closed', 'withdrawn')",
            name="ck_moderation_report_state_allowed",
        ),
        sa.CheckConstraint(
            "(state = 'submitted' AND ended_at IS NULL) OR "
            "(state <> 'submitted' AND ended_at IS NOT NULL)",
            name="ck_moderation_report_state_timestamp_consistent",
        ),
        sa.CheckConstraint(
            "reporter_account_id <> subject_account_id",
            name="ck_moderation_report_different_accounts",
        ),
        sa.CheckConstraint(
            "length(idempotency_key_hash) = 64",
            name="ck_moderation_report_idempotency_hash_valid",
        ),
        sa.CheckConstraint("version >= 1", name="ck_moderation_report_version_positive"),
        sa.ForeignKeyConstraint(["reporter_account_id"], ["account.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_account_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_moderation_report_reporter_idempotency",
        "moderation_report",
        ["reporter_account_id", "idempotency_key_hash"],
        unique=True,
    )
    op.create_index(
        "ix_moderation_report_subject_state",
        "moderation_report",
        ["subject_account_id", "state"],
    )
    op.create_index(
        "ix_moderation_report_reporter_created",
        "moderation_report",
        ["reporter_account_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_moderation_report_reporter_created", table_name="moderation_report")
    op.drop_index("ix_moderation_report_subject_state", table_name="moderation_report")
    op.drop_index("uq_moderation_report_reporter_idempotency", table_name="moderation_report")
    op.drop_table("moderation_report")
