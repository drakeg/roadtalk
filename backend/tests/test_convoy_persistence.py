import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import CheckConstraint, Table

from app.db import Convoy, ConvoyMembership


def test_convoy_constraints_lock_lifecycle_values() -> None:
    convoy_names = {
        c.name for c in cast(Table, Convoy.__table__).constraints if isinstance(c, CheckConstraint)
    }
    membership_names = {
        c.name
        for c in cast(Table, ConvoyMembership.__table__).constraints
        if isinstance(c, CheckConstraint)
    }
    assert {
        "ck_convoy_state_allowed",
        "ck_convoy_display_name_present",
        "ck_convoy_version_positive",
    } <= convoy_names
    assert {
        "ck_convoy_membership_role_allowed",
        "ck_convoy_membership_state_allowed",
        "ck_convoy_membership_state_timestamp_consistent",
        "ck_convoy_membership_version_positive",
    } <= membership_names


def test_convoy_models_store_no_location_or_route_history() -> None:
    fields = {column.name for column in Convoy.__table__.columns} | {
        column.name for column in ConvoyMembership.__table__.columns
    }
    assert not {
        "latitude",
        "longitude",
        "position",
        "location",
        "location_history",
        "route",
        "route_history",
        "heading",
        "speed",
    }.intersection(fields)


def test_terminal_membership_requires_end_timestamp_by_contract() -> None:
    membership = ConvoyMembership(
        id=uuid.uuid4(),
        convoy_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        role="member",
        state="revoked",
        ended_at=datetime.now(UTC),
    )
    assert membership.state == "revoked"
    assert membership.ended_at is not None


def test_relationships_are_bidirectional() -> None:
    assert Convoy.memberships.property.back_populates == "convoy"
    assert ConvoyMembership.convoy.property.back_populates == "memberships"
    assert ConvoyMembership.account.property.back_populates == "convoy_memberships"


def test_only_one_active_convoy_membership_is_allowed_per_account() -> None:
    index = next(
        item
        for item in ConvoyMembership.__table__.indexes
        if item.name == "uq_convoy_membership_one_active_account"
    )
    assert index.unique is True
    assert [column.name for column in index.columns] == ["account_id"]
    assert str(index.dialect_options["postgresql"]["where"]) == "state = 'active'"
