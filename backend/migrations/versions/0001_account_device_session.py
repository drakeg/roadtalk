"""Create account, device, and session foundation.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "account",
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("account_type", sa.String(16), server_default="anonymous", nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "account_type IN ('anonymous', 'registered')",
            name="ck_account_account_type_allowed",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'disabled', 'deleted')",
            name="ck_account_status_allowed",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_account"),
    )
    op.create_table(
        "device",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("installation_id", sa.String(255), nullable=False),
        sa.Column("push_token", sa.Text(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("platform IN ('android', 'ios')", name="ck_device_platform_allowed"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_device_account_id_account",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_device"),
        sa.UniqueConstraint("installation_id", name="uq_device_installation_id"),
    )
    op.create_index("ix_device_account_id", "device", ["account_id"])
    op.create_table(
        "session",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_family_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoke_reason", sa.String(64), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_session_account_id_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
            name="fk_session_device_id_device",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_session"),
        sa.UniqueConstraint("refresh_token_hash", name="uq_session_refresh_token_hash"),
    )
    op.create_index("ix_session_account_id", "session", ["account_id"])
    op.create_index("ix_session_device_id", "session", ["device_id"])
    op.create_index("ix_session_expires_at", "session", ["expires_at"])
    op.create_index("ix_session_refresh_family_id", "session", ["refresh_family_id"])


def downgrade() -> None:
    op.drop_table("session")
    op.drop_table("device")
    op.drop_table("account")
