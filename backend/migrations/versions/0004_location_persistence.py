"""Add foreground consent and current-location persistence.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "location_consent_event",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("disclosure_version", sa.String(32), nullable=False),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "decision IN ('granted', 'revoked')",
            name="ck_location_consent_event_decision_allowed",
        ),
        sa.CheckConstraint(
            "platform IN ('android', 'ios')",
            name="ck_location_consent_event_platform_allowed",
        ),
        sa.CheckConstraint(
            "length(policy_version) > 0",
            name="ck_location_consent_event_policy_version_present",
        ),
        sa.CheckConstraint(
            "length(disclosure_version) > 0",
            name="ck_location_consent_event_disclosure_version_present",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_location_consent_event_account_id_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
            name="fk_location_consent_event_device_id_device",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_location_consent_event"),
    )
    op.create_index(
        "ix_location_consent_event_account_decided",
        "location_consent_event",
        ["account_id", "decided_at"],
    )
    op.create_index(
        "ix_location_consent_event_device_id",
        "location_consent_event",
        ["device_id"],
    )

    op.create_table(
        "current_location",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("source_device_id", sa.Uuid(), nullable=False),
        sa.Column(
            "position",
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizontal_accuracy_m", sa.Float(), nullable=False),
        sa.Column("heading_deg", sa.Float(), nullable=True),
        sa.Column("speed_mps", sa.Float(), nullable=True),
        sa.Column("client_sequence", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consent_policy_version", sa.String(32), nullable=False),
        sa.Column("quality_state", sa.String(16), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "horizontal_accuracy_m >= 0",
            name="ck_current_location_accuracy_nonnegative",
        ),
        sa.CheckConstraint(
            "heading_deg IS NULL OR (heading_deg >= 0 AND heading_deg < 360)",
            name="ck_current_location_heading_range",
        ),
        sa.CheckConstraint(
            "speed_mps IS NULL OR speed_mps >= 0",
            name="ck_current_location_speed_nonnegative",
        ),
        sa.CheckConstraint(
            "client_sequence >= 1",
            name="ck_current_location_client_sequence_positive",
        ),
        sa.CheckConstraint(
            "quality_state IN ('usable', 'degraded')",
            name="ck_current_location_quality_state_allowed",
        ),
        sa.CheckConstraint(
            "length(consent_policy_version) > 0",
            name="ck_current_location_consent_policy_present",
        ),
        sa.CheckConstraint(
            "expires_at > received_at",
            name="ck_current_location_expiry_after_receipt",
        ),
        sa.CheckConstraint("version >= 1", name="ck_current_location_version_positive"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_current_location_account_id_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_device_id"],
            ["device.id"],
            name="fk_current_location_source_device_id_device",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("account_id", name="pk_current_location"),
    )
    op.create_index(
        "ix_current_location_position",
        "current_location",
        ["position"],
        postgresql_using="gist",
    )
    op.create_index(
        "ix_current_location_source_device_id",
        "current_location",
        ["source_device_id"],
    )
    op.create_index(
        "ix_current_location_expires_at",
        "current_location",
        ["expires_at"],
    )
    op.create_index(
        "ix_current_location_effective",
        "current_location",
        ["quality_state", "expires_at"],
    )


def downgrade() -> None:
    op.drop_table("current_location")
    op.drop_table("location_consent_event")
