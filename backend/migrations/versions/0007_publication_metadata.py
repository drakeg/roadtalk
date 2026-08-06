"""Add metadata-only proximity publication state.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "media_grant",
        sa.Column("provider_track_ref", sa.String(128), nullable=True),
    )
    op.add_column(
        "media_grant",
        sa.Column("proximity_policy_version", sa.String(32), nullable=True),
    )
    op.add_column(
        "media_grant",
        sa.Column("eligibility_evaluated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_media_grant_track_ref_present",
        "media_grant",
        "provider_track_ref IS NULL OR length(provider_track_ref) > 0",
    )
    op.create_check_constraint(
        "ck_media_grant_proximity_policy_present",
        "media_grant",
        "proximity_policy_version IS NULL OR length(proximity_policy_version) > 0",
    )
    op.create_check_constraint(
        "ck_media_grant_publication_metadata_consistent",
        "media_grant",
        "(provider_track_ref IS NULL AND proximity_policy_version IS NULL "
        "AND eligibility_evaluated_at IS NULL) OR "
        "(grant_kind = 'transmit' AND provider_track_ref IS NOT NULL "
        "AND proximity_policy_version IS NOT NULL "
        "AND eligibility_evaluated_at IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_media_grant_publication_metadata_consistent",
        "media_grant",
        type_="check",
    )
    op.drop_constraint(
        "ck_media_grant_proximity_policy_present",
        "media_grant",
        type_="check",
    )
    op.drop_constraint(
        "ck_media_grant_track_ref_present",
        "media_grant",
        type_="check",
    )
    op.drop_column("media_grant", "eligibility_evaluated_at")
    op.drop_column("media_grant", "proximity_policy_version")
    op.drop_column("media_grant", "provider_track_ref")
