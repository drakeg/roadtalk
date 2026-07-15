from typing import cast

from sqlalchemy import CheckConstraint, Table

from app.db import Account, Base, Device, Session


def test_active_sprint_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "account",
        "current_location",
        "device",
        "location_consent_event",
        "profile",
        "recovery_credential",
        "session",
    }


def test_account_constraints_protect_enumerated_values() -> None:
    names = {
        constraint.name
        for constraint in cast(Table, Account.__table__).constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert names == {
        "ck_account_account_type_allowed",
        "ck_account_status_allowed",
    }


def test_device_and_session_relationships_are_bidirectional() -> None:
    assert Device.account.property.back_populates == "devices"
    assert Session.account.property.back_populates == "sessions"
    assert Session.device.property.back_populates == "sessions"


def test_lookup_indexes_cover_foreign_keys_and_expiry() -> None:
    device_indexes = {index.name for index in cast(Table, Device.__table__).indexes}
    session_indexes = {index.name for index in cast(Table, Session.__table__).indexes}

    assert "ix_device_account_id" in device_indexes
    assert {
        "ix_session_account_id",
        "ix_session_device_id",
        "ix_session_expires_at",
        "ix_session_refresh_family_id",
    } <= session_indexes
