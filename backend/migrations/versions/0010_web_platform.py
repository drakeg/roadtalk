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
    # Migrations 0001 and 0004 supplied already-prefixed check-constraint names
    # while the metadata naming convention also prefixes check constraints. The
    # resulting PostgreSQL names therefore contain the prefix twice. op.f()
    # marks these as final database names so Alembic does not apply the naming
    # convention a second time while dropping the legacy constraints.
    op.drop_constraint(
        op.f("ck_device_ck_device_platform_allowed"),
        "device",
        type_="check",
    )
    op.create_check_constraint(
        "platform_allowed",
        "device",
        "platform IN ('android', 'ios', 'web')",
    )
    op.drop_constraint(
        op.f("ck_location_consent_event_ck_location_consent_event_platform_allowed"),
        "location_consent_event",
        type_="check",
    )
    op.create_check_constraint(
        "platform_allowed",
        "location_consent_event",
        "platform IN ('android', 'ios', 'web')",
    )


def downgrade() -> None:
    # Revision 0009 cannot represent browser-originated rows. A downgrade must
    # remove those incompatible records before restoring the narrower checks;
    # rewriting them as ios/android would falsify their platform provenance.
    # Delete consent records first because their old platform constraint is
    # restored before the device constraint below. Deleting web devices then
    # lets the existing foreign-key delete behavior clean up device-owned state.
    op.execute("DELETE FROM location_consent_event WHERE platform = 'web'")
    op.execute("DELETE FROM device WHERE platform = 'web'")

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
