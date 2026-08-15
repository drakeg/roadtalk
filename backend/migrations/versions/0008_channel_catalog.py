"""Add server-authoritative channel catalog and selection.

Revision ID: 0008
Revises: 0007
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GENERAL_CHANNEL_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
RV_CHANNEL_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")


def upgrade() -> None:
    op.create_table(
        "channel",
        sa.Column("stable_slug", sa.String(32), nullable=True),
        sa.Column("display_label", sa.String(64), nullable=False),
        sa.Column("channel_type", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("creator_account_id", sa.Uuid(), nullable=True),
        sa.Column("provider_room_ref", sa.String(128), nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "channel_type IN ('public', 'private')",
            name="ck_channel_type_allowed",
        ),
        sa.CheckConstraint(
            "length(display_label) > 0",
            name="ck_channel_display_label_present",
        ),
        sa.CheckConstraint(
            "length(provider_room_ref) > 0",
            name="ck_channel_room_ref_present",
        ),
        sa.CheckConstraint(
            "length(policy_version) > 0",
            name="ck_channel_policy_version_present",
        ),
        sa.CheckConstraint("version >= 1", name="ck_channel_version_positive"),
        sa.CheckConstraint(
            "(channel_type = 'public' AND "
            "((stable_slug = 'general' AND display_label = 'General') OR "
            "(stable_slug = 'rv' AND display_label = 'RV')) "
            "AND creator_account_id IS NULL AND closed_at IS NULL) OR "
            "(channel_type = 'private' AND stable_slug IS NULL "
            "AND creator_account_id IS NOT NULL)",
            name="ck_channel_type_fields_consistent",
        ),
        sa.CheckConstraint(
            "(enabled AND closed_at IS NULL) OR (NOT enabled)",
            name="ck_channel_enabled_not_closed",
        ),
        sa.ForeignKeyConstraint(
            ["creator_account_id"],
            ["account.id"],
            name="fk_channel_creator_account_id_account",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_channel"),
    )
    op.create_index("uq_channel_stable_slug", "channel", ["stable_slug"], unique=True)
    op.create_index(
        "uq_channel_provider_room_ref",
        "channel",
        ["provider_room_ref"],
        unique=True,
    )
    op.create_index(
        "ix_channel_creator_account_id",
        "channel",
        ["creator_account_id"],
    )

    channel_table = sa.table(
        "channel",
        sa.column("id", sa.Uuid()),
        sa.column("stable_slug", sa.String()),
        sa.column("display_label", sa.String()),
        sa.column("channel_type", sa.String()),
        sa.column("enabled", sa.Boolean()),
        sa.column("creator_account_id", sa.Uuid()),
        sa.column("provider_room_ref", sa.String()),
        sa.column("policy_version", sa.String()),
        sa.column("version", sa.Integer()),
    )
    op.bulk_insert(
        channel_table,
        [
            {
                "id": GENERAL_CHANNEL_ID,
                "stable_slug": "general",
                "display_label": "General",
                "channel_type": "public",
                "enabled": True,
                "creator_account_id": None,
                "provider_room_ref": "rm_v1_7WmN4qZ2pL8cH5sT",
                "policy_version": "channel-v1",
                "version": 1,
            },
            {
                "id": RV_CHANNEL_ID,
                "stable_slug": "rv",
                "display_label": "RV",
                "channel_type": "public",
                "enabled": True,
                "creator_account_id": None,
                "provider_room_ref": "rm_v1_3KxR9tB6nQ1dF4yV",
                "policy_version": "channel-v1",
                "version": 1,
            },
        ],
    )

    op.create_table(
        "channel_membership",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(16), server_default=sa.text("'active'"), nullable=False),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "state IN ('active', 'left')",
            name="ck_channel_membership_state_allowed",
        ),
        sa.CheckConstraint(
            "(state = 'active' AND left_at IS NULL) OR (state = 'left' AND left_at IS NOT NULL)",
            name="ck_channel_membership_state_timestamp_consistent",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_channel_membership_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_channel_membership_account_id_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channel.id"],
            name="fk_channel_membership_channel_id_channel",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "account_id",
            "channel_id",
            name="pk_channel_membership",
        ),
    )
    op.create_index(
        "ix_channel_membership_channel_state",
        "channel_membership",
        ["channel_id", "state"],
    )
    op.create_index(
        "ix_channel_membership_account_state",
        "channel_membership",
        ["account_id", "state"],
    )

    op.create_table(
        "channel_selection",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column(
            "selected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_channel_selection_version_positive"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_channel_selection_account_id_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channel.id"],
            name="fk_channel_selection_channel_id_channel",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("account_id", name="pk_channel_selection"),
    )
    op.create_index(
        "ix_channel_selection_channel_id",
        "channel_selection",
        ["channel_id"],
    )
    op.execute(
        sa.text(
            "INSERT INTO channel_selection (account_id, channel_id) "
            "SELECT id, :general_channel_id FROM account"
        ).bindparams(
            sa.bindparam(
                "general_channel_id",
                value=GENERAL_CHANNEL_ID,
                type_=sa.Uuid(),
            )
        )
    )

    op.add_column(
        "media_grant",
        sa.Column("channel_id", sa.Uuid(), nullable=True),
    )
    op.execute(
        sa.text("UPDATE media_grant SET channel_id = :general_channel_id").bindparams(
            sa.bindparam(
                "general_channel_id",
                value=GENERAL_CHANNEL_ID,
                type_=sa.Uuid(),
            )
        )
    )
    op.alter_column("media_grant", "channel_id", nullable=False)
    op.create_foreign_key(
        "fk_media_grant_channel_id_channel",
        "media_grant",
        "channel",
        ["channel_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_media_grant_channel_id", "media_grant", ["channel_id"])


def downgrade() -> None:
    op.drop_index("ix_media_grant_channel_id", table_name="media_grant")
    op.drop_constraint(
        "fk_media_grant_channel_id_channel",
        "media_grant",
        type_="foreignkey",
    )
    op.drop_column("media_grant", "channel_id")
    op.drop_table("channel_selection")
    op.drop_table("channel_membership")
    op.drop_table("channel")
