import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

from geoalchemy2 import Geography, WKTElement
from geoalchemy2.elements import WKBElement
from sqlalchemy import CheckConstraint, Table

from app.db.models import Account, CurrentLocation, Device, LocationConsentEvent


def test_consent_events_are_account_and_device_owned_append_only_records() -> None:
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="ios",
        installation_id="synthetic-installation",
    )
    consent = LocationConsentEvent(
        account=account,
        device=device,
        policy_version="location-v1",
        disclosure_version="location-disclosure-v1",
        platform="ios",
        decision="granted",
        decided_at=datetime.now(UTC),
    )
    table = cast(Table, LocationConsentEvent.__table__)

    assert consent in account.location_consent_events
    assert consent in device.location_consent_events
    assert "updated_at" not in table.c
    assert next(iter(table.c.account_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.device_id.foreign_keys)).ondelete == "CASCADE"


def test_current_location_is_one_row_per_account_with_private_geography() -> None:
    now = datetime.now(UTC)
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="android",
        installation_id="synthetic-installation",
    )
    location = CurrentLocation(
        account=account,
        source_device=device,
        position=cast(WKBElement, WKTElement("POINT(-75 40)", srid=4326)),
        observed_at=now,
        received_at=now,
        horizontal_accuracy_m=12.0,
        heading_deg=90.0,
        speed_mps=4.5,
        client_sequence=1,
        expires_at=now + timedelta(minutes=2),
        consent_policy_version="location-v1",
        quality_state="usable",
        version=1,
    )
    table = cast(Table, CurrentLocation.__table__)

    assert account.current_location is location
    assert location in device.current_locations
    assert list(table.primary_key.columns.keys()) == ["account_id"]
    assert isinstance(table.c.position.type, Geography)
    assert table.c.position.type.geometry_type == "POINT"
    assert table.c.position.type.srid == 4326
    assert table.c.position.type.spatial_index is False
    assert next(iter(table.c.account_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.source_device_id.foreign_keys)).ondelete == "CASCADE"


def test_current_location_constraints_and_indexes_fail_closed() -> None:
    table = cast(Table, CurrentLocation.__table__)
    checks = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    indexes = {str(index.name): index for index in table.indexes}

    assert {
        "ck_current_location_accuracy_nonnegative",
        "ck_current_location_heading_range",
        "ck_current_location_speed_nonnegative",
        "ck_current_location_client_sequence_positive",
        "ck_current_location_quality_state_allowed",
        "ck_current_location_consent_policy_present",
        "ck_current_location_expiry_after_receipt",
        "ck_current_location_version_positive",
    } <= checks
    assert set(indexes) == {
        "ix_current_location_effective",
        "ix_current_location_expires_at",
        "ix_current_location_position",
        "ix_current_location_source_device_id",
    }
    assert indexes["ix_current_location_position"].dialect_options["postgresql"]["using"] == "gist"
    assert [column.name for column in indexes["ix_current_location_effective"].columns] == [
        "quality_state",
        "expires_at",
    ]
