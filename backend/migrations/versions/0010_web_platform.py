"""Allow browser devices for RoadTalk web clients.

Revision ID: 0010_web_platform
Revises: 0009_private_channel_invites
"""

from alembic import op

revision = "0010_web_platform"
down_revision = "0009_private_channel_invites"
branch_labels = None
depends_on = None


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
