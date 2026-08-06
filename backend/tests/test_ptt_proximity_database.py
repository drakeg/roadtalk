import asyncio
import os
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest
from geoalchemy2 import WKTElement
from geoalchemy2.elements import WKBElement
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import (
    Account,
    CurrentLocation,
    Device,
    LocationConsentEvent,
    MediaGrant,
    Session,
)
from app.ptt.proximity import find_eligible_receive_grants, proximity_policy_from_settings


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_proximity_query_enforces_complete_private_receiver_matrix() -> None:
    asyncio.run(_receiver_matrix())


async def _receiver_matrix() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    account_ids: list[uuid.UUID] = []

    try:
        async with factory() as db:
            sender_account, sender_device, _ = await _add_participant(
                db,
                now=now,
                longitude=0,
                latitude=0,
                receive=False,
            )
            account_ids.append(sender_account)
            eligible: set[uuid.UUID] = set()

            for longitude in (0.001, -0.008):
                account_id, _, grant_id = await _add_participant(
                    db, now=now, longitude=longitude, latitude=0
                )
                account_ids.append(account_id)
                assert grant_id is not None
                eligible.add(grant_id)

            variants: tuple[dict[str, Any], ...] = (
                {"longitude": 0.02},
                {"longitude": 0.002, "location_expires_at": now + timedelta(seconds=29)},
                {"longitude": 0.002, "accuracy": 101.0},
                {"longitude": 0.002, "quality": "degraded"},
                {"longitude": 0.002, "consent": "revoked"},
                {"longitude": 0.002, "grant_expires_at": now + timedelta(seconds=29)},
                {"longitude": 0.002, "room_ref": "rm_wrong_opaque_room"},
                {"longitude": 0.002, "account_status": "disabled"},
                {"longitude": 0.002, "session_revoked": True},
                {"longitude": 0.002, "cross_device_location": True},
            )
            for variant in variants:
                account_id, _, _ = await _add_participant(
                    db,
                    now=now,
                    latitude=0,
                    **variant,
                )
                account_ids.append(account_id)
            await db.commit()

            found = await find_eligible_receive_grants(
                db,
                sender_account_id=sender_account,
                sender_device_id=sender_device,
                policy=replace(
                    proximity_policy_from_settings(settings),
                    radius_m=1_000,
                ),
                now=now,
            )

            assert {item.receive_grant_id for item in found} == eligible
            assert all(item.account_id != sender_account for item in found)

            plan = await db.execute(
                text(
                    "EXPLAIN (COSTS OFF) SELECT g.id FROM media_grant g "
                    "JOIN current_location c ON c.account_id = g.account_id "
                    "AND c.source_device_id = g.device_id "
                    "WHERE g.grant_kind = 'receive' AND g.revoked_at IS NULL "
                    "AND ST_DWithin(c.position, "
                    "ST_GeogFromText('SRID=4326;POINT(0 0)'), 1000)"
                )
            )
            encoded_plan = " ".join(str(row[0]) for row in plan).lower()
            assert "st_dwithin" in encoded_plan
            assert "ix_current_location_position" in encoded_plan
    finally:
        async with factory() as db:
            await db.execute(delete(Account).where(Account.id.in_(account_ids)))
            await db.commit()
        await engine.dispose()


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_proximity_boundary_high_latitude_and_antimeridian_are_inclusive() -> None:
    asyncio.run(_geodesic_boundaries())


async def _geodesic_boundaries() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    account_ids: list[uuid.UUID] = []

    try:
        async with factory() as db:
            sender_account, sender_device, _ = await _add_participant(
                db, now=now, longitude=179.999, latitude=80, receive=False
            )
            account_ids.append(sender_account)
            antimeridian_account, _, antimeridian_grant = await _add_participant(
                db, now=now, longitude=-179.999, latitude=80
            )
            account_ids.append(antimeridian_account)
            high_latitude_account, _, high_latitude_grant = await _add_participant(
                db, now=now, longitude=179.999, latitude=80.003
            )
            account_ids.append(high_latitude_account)
            await db.commit()

            distance = await db.scalar(
                select(
                    func.ST_Distance(
                        CurrentLocation.position,
                        func.ST_GeogFromText("SRID=4326;POINT(179.999 80)"),
                    )
                ).where(CurrentLocation.account_id == high_latitude_account)
            )
            assert distance is not None
            found = await find_eligible_receive_grants(
                db,
                sender_account_id=sender_account,
                sender_device_id=sender_device,
                policy=replace(
                    proximity_policy_from_settings(settings),
                    radius_m=float(distance),
                ),
                now=now,
            )

            found_ids = {item.receive_grant_id for item in found}
            assert antimeridian_grant in found_ids
            assert high_latitude_grant in found_ids
    finally:
        async with factory() as db:
            await db.execute(delete(Account).where(Account.id.in_(account_ids)))
            await db.commit()
        await engine.dispose()


async def _add_participant(
    db: AsyncSession,
    *,
    now: datetime,
    longitude: float,
    latitude: float,
    receive: bool = True,
    location_expires_at: datetime | None = None,
    accuracy: float = 10,
    quality: str = "usable",
    consent: str = "granted",
    grant_expires_at: datetime | None = None,
    room_ref: str = "rm_7f3d2c9a1b6e4d08",
    account_status: str = "active",
    session_revoked: bool = False,
    cross_device_location: bool = False,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID | None]:
    account = Account(status=account_status)
    device = Device(
        account=account,
        platform="ios",
        installation_id=f"proximity-{uuid.uuid4()}",
    )
    db.add_all([account, device])
    await db.flush()
    location_device = device
    if cross_device_location:
        location_device = Device(
            account=account,
            platform="ios",
            installation_id=f"proximity-location-{uuid.uuid4()}",
        )
        db.add(location_device)
        await db.flush()
    db.add(
        Session(
            account_id=account.id,
            device_id=device.id,
            refresh_token_hash=f"proximity-refresh-{uuid.uuid4()}",
            expires_at=(now + timedelta(minutes=10)).replace(tzinfo=None),
            revoked_at=now.replace(tzinfo=None) if session_revoked else None,
            revoke_reason="synthetic" if session_revoked else None,
        )
    )
    db.add(
        LocationConsentEvent(
            account_id=account.id,
            device_id=location_device.id,
            policy_version="location-v1",
            disclosure_version="location-disclosure-v1",
            platform="ios",
            decision=consent,
            decided_at=now,
        )
    )
    db.add(
        CurrentLocation(
            account_id=account.id,
            source_device_id=location_device.id,
            position=cast(
                WKBElement,
                WKTElement(f"POINT({longitude} {latitude})", srid=4326),
            ),
            observed_at=now,
            received_at=now,
            horizontal_accuracy_m=accuracy,
            heading_deg=None,
            speed_mps=None,
            client_sequence=1,
            expires_at=location_expires_at or now + timedelta(minutes=2),
            consent_policy_version="location-v1",
            quality_state=quality,
            version=1,
        )
    )
    grant_id: uuid.UUID | None = None
    if receive:
        grant = MediaGrant(
            account_id=account.id,
            device_id=device.id,
            grant_kind="receive",
            provider="livekit",
            provider_room_ref=room_ref,
            provider_participant_ref=f"participant_{uuid.uuid4().hex}",
            action_scope="subscribe",
            policy_version="ptt-v1",
            idempotency_key_hash="a" * 64,
            request_fingerprint="b" * 64,
            issued_at=now,
            expires_at=grant_expires_at or now + timedelta(minutes=5),
            revoked_at=None,
            outcome_code="issued",
        )
        db.add(grant)
        await db.flush()
        grant_id = grant.id
    return account.id, device.id, grant_id
