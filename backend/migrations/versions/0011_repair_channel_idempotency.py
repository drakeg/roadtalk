"""Repair channel idempotency schema drift in persistent local databases.

Revision ID: 0011
Revises: 0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CREATE_IDEMPOTENCY_INDEX = "uq_channel_creator_create_idempotency"


def upgrade() -> None:
    """Reconcile databases that recorded 0009 before its final schema was present."""
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("channel")}

    if "create_idempotency_hash" not in columns:
        op.add_column(
            "channel",
            sa.Column("create_idempotency_hash", sa.String(64), nullable=True),
        )
    if "create_request_fingerprint" not in columns:
        op.add_column(
            "channel",
            sa.Column("create_request_fingerprint", sa.String(64), nullable=True),
        )

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("channel")}
    if _CREATE_IDEMPOTENCY_INDEX not in indexes:
        op.create_index(
            _CREATE_IDEMPOTENCY_INDEX,
            "channel",
            ["creator_account_id", "create_idempotency_hash"],
            unique=True,
        )


def downgrade() -> None:
    # These objects belong to migration 0009. Removing them while downgrading only
    # the reconciliation revision would corrupt a canonical database, so 0011 is
    # intentionally forward-only.
    pass
