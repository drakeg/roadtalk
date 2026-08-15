"""Add private-channel invite persistence.

Revision ID: 0009
Revises: 0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("channel", sa.Column("create_idempotency_hash", sa.String(64), nullable=True))
    op.add_column("channel", sa.Column("create_request_fingerprint", sa.String(64), nullable=True))
    op.create_index(
        "uq_channel_creator_create_idempotency",
        "channel",
        ["creator_account_id", "create_idempotency_hash"],
        unique=True,
    )
    op.create_table(
        "channel_invite",
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("secret_hash", sa.String(255), nullable=False),
        sa.Column("fingerprint", sa.String(12), nullable=False),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rotation_idempotency_hash", sa.String(64), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "length(secret_hash) >= 64", name="ck_channel_invite_secret_hash_present"
        ),
        sa.CheckConstraint("length(fingerprint) = 12", name="ck_channel_invite_fingerprint_valid"),
        sa.CheckConstraint("version >= 1", name="ck_channel_invite_version_positive"),
        sa.ForeignKeyConstraint(["channel_id"], ["channel.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("channel_id", name="pk_channel_invite"),
    )
    op.create_index("ix_channel_invite_fingerprint", "channel_invite", ["fingerprint"])


def downgrade() -> None:
    op.drop_table("channel_invite")
    op.drop_index("uq_channel_creator_create_idempotency", table_name="channel")
    op.drop_column("channel", "create_request_fingerprint")
    op.drop_column("channel", "create_idempotency_hash")
