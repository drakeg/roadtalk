"""Add durable PTT grant idempotency metadata.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "media_grant",
        sa.Column("idempotency_key_hash", sa.String(64), nullable=False),
    )
    op.add_column(
        "media_grant",
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
    )
    op.create_check_constraint(
        "ck_media_grant_idempotency_hash_valid",
        "media_grant",
        "length(idempotency_key_hash) = 64",
    )
    op.create_check_constraint(
        "ck_media_grant_request_fingerprint_valid",
        "media_grant",
        "length(request_fingerprint) = 64",
    )
    op.create_index(
        "uq_media_grant_account_kind_idempotency",
        "media_grant",
        ["account_id", "grant_kind", "idempotency_key_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_media_grant_account_kind_idempotency", table_name="media_grant")
    op.drop_constraint(
        "ck_media_grant_request_fingerprint_valid",
        "media_grant",
        type_="check",
    )
    op.drop_constraint(
        "ck_media_grant_idempotency_hash_valid",
        "media_grant",
        type_="check",
    )
    op.drop_column("media_grant", "request_fingerprint")
    op.drop_column("media_grant", "idempotency_key_hash")
