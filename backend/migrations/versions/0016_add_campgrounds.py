"""Add deterministic campground catalog.

Revision ID: 0016
Revises: 0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campground",
        sa.Column("campground_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("locality", sa.String(96), nullable=False),
        sa.Column("region", sa.String(64), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("electric", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("water", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("sewer", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("dump_station", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("wifi", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("showers", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("laundry", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("pet_friendly", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("source", sa.String(32), server_default="deterministic_local", nullable=False),
        sa.Column("freshness", sa.String(32), server_default="deterministic", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "category IN ('public', 'private', 'state_park', 'national_park', "
            "'county_municipal', 'other')",
            name="ck_campground_category_allowed",
        ),
        sa.CheckConstraint(
            "length(country_code) = 2 AND upper(country_code) = country_code",
            name="ck_campground_country_code",
        ),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_campground_latitude"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_campground_longitude"),
        sa.CheckConstraint("source = 'deterministic_local'", name="ck_campground_source"),
        sa.CheckConstraint("freshness = 'deterministic'", name="ck_campground_freshness"),
        sa.PrimaryKeyConstraint("campground_id"),
    )
    op.create_index("ix_campground_name", "campground", ["name"])
    op.create_index("ix_campground_region_category", "campground", ["region", "category"])


def downgrade() -> None:
    op.drop_index("ix_campground_region_category", table_name="campground")
    op.drop_index("ix_campground_name", table_name="campground")
    op.drop_table("campground")
