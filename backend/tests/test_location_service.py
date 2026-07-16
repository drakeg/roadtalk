import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CurrentLocation
from app.location.quality import LocationPolicy, LocationPolicyError, LocationSample
from app.location.service import (
    delete_current_location,
    delete_expired_locations,
    record_current_location,
)


def policy() -> LocationPolicy:
    return LocationPolicy(
        version="location-v1",
        max_sample_age_seconds=60,
        max_future_seconds=10,
        max_usable_accuracy_m=100,
        max_retained_accuracy_m=1_000,
        max_reported_speed_mps=100,
        max_plausible_speed_mps=100,
        plausibility_slack_m=250,
        usable_ttl_seconds=120,
        degraded_ttl_seconds=60,
        cross_device_newer_seconds=1,
    )


def sample(now: datetime, *, sequence: int = 1) -> LocationSample:
    return LocationSample(
        latitude=40.0,
        longitude=-75.0,
        observed_at=now,
        horizontal_accuracy_m=10,
        heading_deg=45,
        speed_mps=3,
        client_sequence=sequence,
        consent_policy_version="location-v1",
    )


def session() -> tuple[AsyncSession, MagicMock]:
    raw = MagicMock()
    raw.commit = AsyncMock()
    raw.rollback = AsyncMock()
    raw.scalar = AsyncMock()
    raw.scalars = AsyncMock()
    return cast(AsyncSession, raw), raw


def allow_preconditions(monkeypatch: pytest.MonkeyPatch, *, locked: object = None) -> None:
    monkeypatch.setattr(
        "app.location.service._require_source_ownership",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.location.service._require_current_consent",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.location.service._locked_current_location",
        AsyncMock(return_value=locked),
    )


def test_record_current_location_inserts_metadata_only_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_record_current_location_inserts_metadata_only_receipt(monkeypatch))


async def _record_current_location_inserts_metadata_only_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)
    db, raw = session()
    allow_preconditions(monkeypatch)

    receipt = await record_current_location(
        db,
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        sample=sample(now),
        policy=policy(),
        now=now,
    )

    assert receipt.accepted_sequence == 1
    assert receipt.quality_state == "usable"
    assert receipt.expires_at == now + timedelta(seconds=120)
    assert receipt.policy_version == "location-v1"
    assert receipt.version == 1
    raw.add.assert_called_once()
    raw.commit.assert_awaited_once()


def test_record_current_location_replaces_locked_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_record_current_location_replaces_locked_row(monkeypatch))


async def _record_current_location_replaces_locked_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)
    account_id = uuid.uuid4()
    device_id = uuid.uuid4()
    current = CurrentLocation(
        account_id=account_id,
        source_device_id=device_id,
        position=WKTElement("POINT(-75 40)", srid=4326),
        observed_at=now - timedelta(seconds=2),
        received_at=now - timedelta(seconds=2),
        horizontal_accuracy_m=10,
        heading_deg=None,
        speed_mps=None,
        client_sequence=1,
        expires_at=now + timedelta(seconds=100),
        consent_policy_version="location-v1",
        quality_state="usable",
        version=1,
    )
    db, raw = session()
    allow_preconditions(monkeypatch, locked=(current, 40.0, -75.0))

    receipt = await record_current_location(
        db,
        account_id=account_id,
        device_id=device_id,
        sample=sample(now, sequence=2),
        policy=policy(),
        now=now,
    )

    assert receipt.version == 2
    assert current.client_sequence == 2
    raw.add.assert_not_called()


def test_record_current_location_rolls_back_insert_race(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_record_current_location_rolls_back_insert_race(monkeypatch))


async def _record_current_location_rolls_back_insert_race(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)
    db, raw = session()
    raw.commit.side_effect = IntegrityError("insert", {}, RuntimeError("conflict"))
    allow_preconditions(monkeypatch)

    with pytest.raises(LocationPolicyError) as raised:
        await record_current_location(
            db,
            account_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
            sample=sample(now),
            policy=policy(),
            now=now,
        )

    assert raised.value.code == "LOCATION_SAMPLE_CONFLICT"
    raw.rollback.assert_awaited_once()


def test_location_deletion_helpers_are_idempotent() -> None:
    asyncio.run(_location_deletion_helpers_are_idempotent())


async def _location_deletion_helpers_are_idempotent() -> None:
    db, raw = session()
    deleted = MagicMock()
    deleted.all.return_value = [uuid.uuid4(), uuid.uuid4()]
    raw.scalars.return_value = deleted
    raw.scalar.side_effect = [uuid.uuid4(), None]

    assert await delete_expired_locations(db) == 2
    assert await delete_current_location(db, account_id=uuid.uuid4()) is True
    assert await delete_current_location(db, account_id=uuid.uuid4()) is False
    assert raw.commit.await_count == 3
