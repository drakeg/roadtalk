import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from geoalchemy2 import WKTElement
from geoalchemy2.elements import WKBElement
from sqlalchemy import delete, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, CurrentLocation, Device, LocationConsentEvent
from app.location.nearby import NearbySummaryError, get_nearby_summary


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_nearby_summary_uses_private_indexed_postgis_eligibility() -> None:
    asyncio.run(_nearby_lifecycle())


async def _nearby_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    account_ids: list[uuid.UUID] = []

    try:
        async with factory() as db:
            caller = await _add_location(db, now=now, longitude=0, latitude=0)
            account_ids.append(caller)
            await db.commit()
            empty = await get_nearby_summary(
                db,
                account_id=caller,
                policy_version=settings.location_policy_version,
                max_usable_accuracy_m=100,
                radius_m=1_000,
                many_threshold=2,
                now=now,
            )
            assert empty.bucket == "none"

            account_ids.append(await _add_location(db, now=now, longitude=0.00897, latitude=0))
            account_ids.append(await _add_location(db, now=now, longitude=0.009, latitude=0))
            account_ids.append(
                await _add_location(
                    db,
                    now=now,
                    longitude=0.004,
                    latitude=0,
                    expires_at=now,
                )
            )
            account_ids.append(
                await _add_location(
                    db,
                    now=now,
                    longitude=0.003,
                    latitude=0,
                    accuracy=500,
                )
            )
            account_ids.append(
                await _add_location(
                    db,
                    now=now,
                    longitude=0.002,
                    latitude=0,
                    quality="degraded",
                )
            )
            account_ids.append(
                await _add_location(
                    db,
                    now=now,
                    longitude=0.001,
                    latitude=0,
                    revoked=True,
                )
            )
            await db.commit()

            summary = await get_nearby_summary(
                db,
                account_id=caller,
                policy_version=settings.location_policy_version,
                max_usable_accuracy_m=100,
                radius_m=1_000,
                many_threshold=2,
                now=now,
            )
            assert summary.bucket == "few"
            assert set(summary.__dict__) == {
                "availability",
                "bucket",
                "freshness",
                "expires_at",
            }

            second_inside = await _add_location(db, now=now, longitude=-0.00897, latitude=0)
            account_ids.append(second_inside)
            await db.commit()
            many = await get_nearby_summary(
                db,
                account_id=caller,
                policy_version=settings.location_policy_version,
                max_usable_accuracy_m=100,
                radius_m=1_000,
                many_threshold=2,
                now=now,
            )
            assert many.bucket == "many"

            await db.execute(text("SET LOCAL enable_seqscan = off"))
            plan = await db.execute(
                text(
                    "EXPLAIN (COSTS OFF) SELECT count(*) FROM current_location c "
                    "WHERE c.account_id <> :caller "
                    "AND c.quality_state = 'usable' AND c.expires_at > :now "
                    "AND c.horizontal_accuracy_m <= 100 "
                    "AND c.consent_policy_version = 'location-v1' "
                    "AND EXISTS (SELECT 1 FROM location_consent_event e "
                    "WHERE e.id = (SELECT latest.id FROM location_consent_event latest "
                    "WHERE latest.account_id = c.account_id "
                    "ORDER BY latest.decided_at DESC, latest.created_at DESC, latest.id DESC "
                    "LIMIT 1) AND e.decision = 'granted' "
                    "AND e.policy_version = 'location-v1') "
                    "AND ST_DWithin(c.position, "
                    "ST_GeogFromText('SRID=4326;POINT(0 0)'), 1000)"
                ),
                {"caller": caller, "now": now},
            )
            encoded_plan = " ".join(str(row[0]) for row in plan).lower()
            assert "ix_current_location_position" in encoded_plan

            for values in (
                {"quality_state": "degraded"},
                {"quality_state": "usable", "horizontal_accuracy_m": 500},
                {"horizontal_accuracy_m": 10, "expires_at": now},
            ):
                await db.execute(
                    update(CurrentLocation)
                    .where(CurrentLocation.account_id == caller)
                    .values(**values)
                )
                await db.commit()
                with pytest.raises(NearbySummaryError):
                    await get_nearby_summary(
                        db,
                        account_id=caller,
                        policy_version=settings.location_policy_version,
                        max_usable_accuracy_m=100,
                        radius_m=1_000,
                        many_threshold=2,
                        now=now,
                    )

            await db.execute(
                update(CurrentLocation)
                .where(CurrentLocation.account_id == caller)
                .values(
                    quality_state="usable",
                    horizontal_accuracy_m=10,
                    expires_at=now + timedelta(seconds=120),
                )
            )
            caller_device = await db.scalar(
                text("SELECT source_device_id FROM current_location WHERE account_id = :caller"),
                {"caller": caller},
            )
            db.add(
                LocationConsentEvent(
                    account_id=caller,
                    device_id=caller_device,
                    policy_version="location-v1",
                    disclosure_version="location-disclosure-v1",
                    platform="ios",
                    decision="revoked",
                    decided_at=now,
                )
            )
            await db.commit()
            with pytest.raises(NearbySummaryError):
                await get_nearby_summary(
                    db,
                    account_id=caller,
                    policy_version=settings.location_policy_version,
                    max_usable_accuracy_m=100,
                    radius_m=1_000,
                    many_threshold=2,
                    now=now,
                )

            await db.execute(delete(CurrentLocation).where(CurrentLocation.account_id == caller))
            await db.commit()
            with pytest.raises(NearbySummaryError):
                await get_nearby_summary(
                    db,
                    account_id=caller,
                    policy_version=settings.location_policy_version,
                    max_usable_accuracy_m=100,
                    radius_m=1_000,
                    many_threshold=2,
                    now=now,
                )
    finally:
        async with factory() as db:
            await db.execute(delete(Account).where(Account.id.in_(account_ids)))
            await db.commit()
        await engine.dispose()


async def _add_location(
    db: AsyncSession,
    *,
    now: datetime,
    longitude: float,
    latitude: float,
    expires_at: datetime | None = None,
    accuracy: float = 10,
    quality: str = "usable",
    revoked: bool = False,
) -> uuid.UUID:
    account = Account()
    device = Device(
        account=account,
        platform="ios",
        installation_id=f"nearby-{uuid.uuid4()}",
    )
    db.add_all([account, device])
    await db.flush()
    grant = LocationConsentEvent(
        account_id=account.id,
        device_id=device.id,
        policy_version="location-v1",
        disclosure_version="location-disclosure-v1",
        platform="ios",
        decision="granted",
        decided_at=now - timedelta(seconds=10),
    )
    db.add(grant)
    if revoked:
        db.add(
            LocationConsentEvent(
                account_id=account.id,
                device_id=device.id,
                policy_version="location-v1",
                disclosure_version="location-disclosure-v1",
                platform="ios",
                decision="revoked",
                decided_at=now,
            )
        )
    db.add(
        CurrentLocation(
            account_id=account.id,
            source_device_id=device.id,
            position=cast(
                WKBElement,
                WKTElement(f"POINT({longitude} {latitude})", srid=4326),
            ),
            observed_at=now - timedelta(seconds=1),
            received_at=now - timedelta(seconds=1),
            horizontal_accuracy_m=accuracy,
            heading_deg=None,
            speed_mps=None,
            client_sequence=1,
            expires_at=expires_at or now + timedelta(seconds=120),
            consent_policy_version="location-v1",
            quality_state=quality,
            version=1,
        )
    )
    return account.id
