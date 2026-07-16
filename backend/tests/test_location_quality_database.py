import asyncio
import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, CurrentLocation, Device, LocationConsentEvent
from app.location.quality import LocationPolicyError, LocationSample, policy_from_settings
from app.location.service import (
    delete_current_location,
    delete_expired_locations,
    record_current_location,
)


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_location_quality_replacement_consent_and_expiry_lifecycle() -> None:
    asyncio.run(_quality_lifecycle())


async def _quality_lifecycle() -> None:
    settings = Settings(environment="test")
    policy = policy_from_settings(settings)
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    account = Account()
    first_device = Device(
        account=account,
        platform="ios",
        installation_id=f"quality-first-{now.timestamp()}",
    )
    second_device = Device(
        account=account,
        platform="android",
        installation_id=f"quality-second-{now.timestamp()}",
    )

    try:
        async with factory() as db:
            db.add_all([account, first_device, second_device])
            await db.flush()
            db.add(
                LocationConsentEvent(
                    account_id=account.id,
                    device_id=first_device.id,
                    policy_version=policy.version,
                    disclosure_version="location-disclosure-v1",
                    platform="ios",
                    decision="granted",
                    decided_at=now,
                )
            )
            await db.commit()

            first = await record_current_location(
                db,
                account_id=account.id,
                device_id=first_device.id,
                sample=LocationSample(
                    latitude=40.0,
                    longitude=-75.0,
                    observed_at=now,
                    horizontal_accuracy_m=10,
                    heading_deg=45,
                    speed_mps=3,
                    client_sequence=1,
                    consent_policy_version=policy.version,
                ),
                policy=policy,
                now=now,
            )
            assert first.version == 1
            assert first.quality_state == "usable"

            with pytest.raises(LocationPolicyError) as replayed:
                await record_current_location(
                    db,
                    account_id=account.id,
                    device_id=first_device.id,
                    sample=LocationSample(
                        latitude=40.0,
                        longitude=-75.0,
                        observed_at=now,
                        horizontal_accuracy_m=10,
                        heading_deg=None,
                        speed_mps=None,
                        client_sequence=1,
                        consent_policy_version=policy.version,
                    ),
                    policy=policy,
                    now=now + timedelta(seconds=1),
                )
            assert replayed.value.code == "LOCATION_SAMPLE_OUT_OF_ORDER"

            replacement_time = now + timedelta(seconds=2)
            replacement = await record_current_location(
                db,
                account_id=account.id,
                device_id=second_device.id,
                sample=LocationSample(
                    latitude=40.0001,
                    longitude=-75.0,
                    observed_at=replacement_time,
                    horizontal_accuracy_m=150,
                    heading_deg=None,
                    speed_mps=None,
                    client_sequence=1,
                    consent_policy_version=policy.version,
                ),
                policy=policy,
                now=replacement_time,
            )
            assert replacement.version == 2
            assert replacement.quality_state == "degraded"
            stored = await db.scalar(
                select(CurrentLocation).where(CurrentLocation.account_id == account.id)
            )
            assert stored is not None
            assert stored.source_device_id == second_device.id

            with pytest.raises(LocationPolicyError) as implausible:
                await record_current_location(
                    db,
                    account_id=account.id,
                    device_id=second_device.id,
                    sample=LocationSample(
                        latitude=50.0,
                        longitude=-65.0,
                        observed_at=replacement_time + timedelta(seconds=1),
                        horizontal_accuracy_m=10,
                        heading_deg=None,
                        speed_mps=None,
                        client_sequence=2,
                        consent_policy_version=policy.version,
                    ),
                    policy=policy,
                    now=replacement_time + timedelta(seconds=1),
                )
            assert implausible.value.code == "LOCATION_MOVEMENT_IMPLAUSIBLE"

            assert await delete_current_location(db, account_id=account.id) is True
            assert await delete_current_location(db, account_id=account.id) is False

            resumed_time = replacement_time + timedelta(seconds=2)
            resumed = await record_current_location(
                db,
                account_id=account.id,
                device_id=second_device.id,
                sample=LocationSample(
                    latitude=40.0001,
                    longitude=-75.0,
                    observed_at=resumed_time,
                    horizontal_accuracy_m=10,
                    heading_deg=None,
                    speed_mps=None,
                    client_sequence=2,
                    consent_policy_version=policy.version,
                ),
                policy=policy,
                now=resumed_time,
            )
            assert await delete_expired_locations(db, now=resumed.expires_at) == 1
            assert await delete_expired_locations(db, now=resumed.expires_at) == 0

            db.add(
                LocationConsentEvent(
                    account_id=account.id,
                    device_id=second_device.id,
                    policy_version=policy.version,
                    disclosure_version="location-disclosure-v1",
                    platform="android",
                    decision="revoked",
                    decided_at=now + timedelta(seconds=3),
                )
            )
            await db.commit()
            with pytest.raises(LocationPolicyError) as withdrawn:
                await record_current_location(
                    db,
                    account_id=account.id,
                    device_id=second_device.id,
                    sample=LocationSample(
                        latitude=40.0,
                        longitude=-75.0,
                        observed_at=now + timedelta(seconds=4),
                        horizontal_accuracy_m=10,
                        heading_deg=None,
                        speed_mps=None,
                        client_sequence=2,
                        consent_policy_version=policy.version,
                    ),
                    policy=policy,
                    now=now + timedelta(seconds=4),
                )
            assert withdrawn.value.code == "LOCATION_CONSENT_REQUIRED"
            assert await delete_current_location(db, account_id=account.id) is False
    finally:
        await engine.dispose()
