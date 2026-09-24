"""Harden Sprint 11 convoy membership invariants.

Revision ID: 0020
Revises: 0019
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_convoy_membership_one_active_account",
        "convoy_membership",
        ["account_id"],
        unique=True,
        postgresql_where=sa.text("state = 'active'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_convoy_membership_one_active_account",
        table_name="convoy_membership",
    )
