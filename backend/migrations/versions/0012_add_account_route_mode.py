"""Add versioned account route-mode selection.

Revision ID: 0012
Revises: 0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_route_mode",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(16), server_default="nearby", nullable=False),
        sa.Column(
            "selected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("mode IN ('nearby', 'same_road')", name="ck_account_route_mode_mode_allowed"),
        sa.CheckConstraint("version >= 1", name="ck_account_route_mode_version_positive"),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("account_id"),
    )


def downgrade() -> None:
    op.drop_table("account_route_mode")
