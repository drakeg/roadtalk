"""Add metadata-only PTT media grants.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "media_grant",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("parent_grant_id", sa.Uuid(), nullable=True),
        sa.Column("grant_kind", sa.String(16), nullable=False),
        sa.Column("provider", sa.String(16), server_default=sa.text("'livekit'"), nullable=False),
        sa.Column("provider_room_ref", sa.String(128), nullable=False),
        sa.Column("provider_participant_ref", sa.String(128), nullable=False),
        sa.Column("action_scope", sa.String(32), nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome_code", sa.String(64), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "grant_kind IN ('receive', 'transmit')",
            name="ck_media_grant_grant_kind_allowed",
        ),
        sa.CheckConstraint(
            "provider = 'livekit'",
            name="ck_media_grant_provider_allowed",
        ),
        sa.CheckConstraint(
            "(grant_kind = 'receive' AND action_scope = 'subscribe') OR "
            "(grant_kind = 'transmit' AND action_scope = 'microphone_publish')",
            name="ck_media_grant_kind_scope_consistent",
        ),
        sa.CheckConstraint(
            "(grant_kind = 'receive' AND parent_grant_id IS NULL) OR "
            "(grant_kind = 'transmit' AND parent_grant_id IS NOT NULL)",
            name="ck_media_grant_parent_consistent",
        ),
        sa.CheckConstraint(
            "length(provider_room_ref) > 0",
            name="ck_media_grant_room_ref_present",
        ),
        sa.CheckConstraint(
            "length(provider_participant_ref) > 0",
            name="ck_media_grant_participant_ref_present",
        ),
        sa.CheckConstraint(
            "length(policy_version) > 0",
            name="ck_media_grant_policy_version_present",
        ),
        sa.CheckConstraint(
            "expires_at > issued_at",
            name="ck_media_grant_expiry_after_issue",
        ),
        sa.CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= issued_at",
            name="ck_media_grant_revocation_after_issue",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_media_grant_account_id_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
            name="fk_media_grant_device_id_device",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_grant_id"],
            ["media_grant.id"],
            name="fk_media_grant_parent_grant_id_media_grant",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_media_grant"),
    )
    op.create_index(
        "ix_media_grant_account_kind_expires",
        "media_grant",
        ["account_id", "grant_kind", "expires_at"],
    )
    op.create_index("ix_media_grant_device_id", "media_grant", ["device_id"])
    op.create_index(
        "ix_media_grant_parent_grant_id",
        "media_grant",
        ["parent_grant_id"],
    )
    op.create_index(
        "ix_media_grant_provider_participant",
        "media_grant",
        ["provider_room_ref", "provider_participant_ref"],
    )


def downgrade() -> None:
    op.drop_table("media_grant")
