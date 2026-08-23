"""Add minimized current route-context persistence.

Revision ID: 0013
Revises: 0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "current_route_context",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("corridor_digest", sa.String(64), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("confidence", sa.String(16), nullable=False),
        sa.Column("source_location_version", sa.Integer(), nullable=False),
        sa.Column("provider_version", sa.String(32), nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "length(corridor_digest) = 64",
            name="ck_current_route_context_corridor_digest_length",
        ),
        sa.CheckConstraint(
            "direction IN ('north', 'northeast', 'east', 'southeast', 'south', "
            "'southwest', 'west', 'northwest', 'stationary', 'unknown')",
            name="ck_current_route_context_direction_allowed",
        ),
        sa.CheckConstraint(
            "confidence = 'confident'",
            name="ck_current_route_context_confidence_confident_only",
        ),
        sa.CheckConstraint(
            "source_location_version >= 1",
            name="ck_current_route_context_source_location_version_positive",
        ),
        sa.CheckConstraint(
            "length(provider_version) > 0",
            name="ck_current_route_context_provider_version_present",
        ),
        sa.CheckConstraint(
            "length(policy_version) > 0",
            name="ck_current_route_context_policy_version_present",
        ),
        sa.CheckConstraint(
            "expires_at > matched_at",
            name="ck_current_route_context_expiry_after_match",
        ),
        sa.CheckConstraint("version >= 1", name="ck_current_route_context_version_positive"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["current_location.account_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_index(
        "ix_current_route_context_expires_at",
        "current_route_context",
        ["expires_at"],
    )
    op.create_index(
        "ix_current_route_context_corridor_direction",
        "current_route_context",
        ["corridor_digest", "direction", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_current_route_context_corridor_direction",
        table_name="current_route_context",
    )
    op.drop_index("ix_current_route_context_expires_at", table_name="current_route_context")
    op.drop_table("current_route_context")
