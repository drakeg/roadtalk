"""Allow browser devices for RoadTalk web clients.

Revision ID: 0010
Revises: 0009
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("platform_allowed", "device", type_="check")
    op.create_check_constraint(
        "platform_allowed",
        "device",
        "platform IN ('android', 'ios', 'web')",
    )
    op.drop_constraint("platform_allowed", "location_consent_event", type_="check")
    op.create_check_constraint(
        "platform_allowed",
        "location_consent_event",
        "platform IN ('android', 'ios', 'web')",
    )


def downgrade() -> None:
    op.drop_constraint("platform_allowed", "location_consent_event", type_="check")
    op.create_check_constraint(
        "platform_allowed",
        "location_consent_event",
        "platform IN ('android', 'ios')",
    )
    op.drop_constraint("platform_allowed", "device", type_="check")
    op.create_check_constraint(
        "platform_allowed",
        "device",
        "platform IN ('android', 'ios')",
    )
