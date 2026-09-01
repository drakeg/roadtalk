"""Add bounded account-owned notifications and preferences.

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("channel_activity_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("urgent_alert_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_notification_preferences_version_positive"),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_table(
        "notification",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("notification_class", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("title", sa.String(96), nullable=True),
        sa.Column("message", sa.String(280), nullable=False),
        sa.Column("channel_label", sa.String(64), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "notification_class IN ('account', 'channel_activity', 'urgent_alert')",
            name="ck_notification_class_allowed",
        ),
        sa.CheckConstraint(
            "priority IN ('normal', 'high', 'urgent')",
            name="ck_notification_priority_allowed",
        ),
        sa.CheckConstraint(
            "source IN ('roadtalk_account', 'roadtalk_channel', 'user_generated_urgent')",
            name="ck_notification_source_allowed",
        ),
        sa.CheckConstraint("expires_at > issued_at", name="ck_notification_expiry_after_issue"),
        sa.CheckConstraint("version >= 1", name="ck_notification_version_positive"),
        sa.CheckConstraint(
            "(notification_class = 'account' AND title IS NOT NULL "
            "AND channel_label IS NULL) OR "
            "(notification_class = 'channel_activity' AND title IS NOT NULL "
            "AND channel_label IS NOT NULL) OR "
            "(notification_class = 'urgent_alert' AND title IS NULL "
            "AND channel_label IS NULL)",
            name="ck_notification_class_fields_consistent",
        ),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_account_expires",
        "notification",
        ["account_id", "expires_at"],
    )
    op.create_index(
        "ix_notification_account_issued",
        "notification",
        ["account_id", "issued_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_account_issued", table_name="notification")
    op.drop_index("ix_notification_account_expires", table_name="notification")
    op.drop_table("notification")
    op.drop_table("notification_preferences")
