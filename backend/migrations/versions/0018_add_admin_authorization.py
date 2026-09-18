"""Add administrator authorization and audit metadata.

Revision ID: 0018
Revises: 0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "account",
        sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_table(
        "admin_audit_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_account_id", sa.Uuid(), nullable=False),
        sa.Column("target_account_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_account_id"], ["account.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_account_id"], ["account.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "action IN ('account_disabled', 'account_enabled', 'sessions_revoked')",
            name="ck_admin_audit_event_action_allowed",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_audit_event_target_created",
        "admin_audit_event",
        ["target_account_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_event_target_created", table_name="admin_audit_event")
    op.drop_table("admin_audit_event")
    op.drop_column("account", "is_admin")
