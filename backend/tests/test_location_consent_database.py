import asyncio
import os
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, CurrentLocation, Device, LocationConsentEvent
from app.location.consent import LocationConsentError, set_foreground_location_consent
from app.location.quality import LocationSample, policy_from_settings
from app.location.service import record_current_location


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_foreground_consent_is_idempotent_versioned_and_deletes_location() -> None:
    asyncio.run(_consent_lifecycle())


async def _consent_lifecycle() -> None:
    settings = Settings(environment="test")
    policy = policy_from_settings(settings)
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    account = Account()
    device = Device(
        account=account,
        platform="ios",
        installation_id=f"consent-api-{now.timestamp()}",
    )

    try:
        async with factory() as db:
            db.add_all([account, device])
            await db.commit()

            grant = await set_foreground_location_consent(
                db,
                account_id=account.id,
                device_id=device.id,
                platform=device.platform,
                decision="granted",
                requested_policy_version=policy.version,
                requested_disclosure_version=settings.location_disclosure_version,
                current_policy_version=policy.version,
                current_disclosure_version=settings.location_disclosure_version,
                now=now,
            )
            replay = await set_foreground_location_consent(
                db,
                account_id=account.id,
                device_id=device.id,
                platform=device.platform,
                decision="granted",
                requested_policy_version=policy.version,
                requested_disclosure_version=settings.location_disclosure_version,
                current_policy_version=policy.version,
                current_disclosure_version=settings.location_disclosure_version,
                now=now,
            )
            assert replay == grant
            assert await _consent_count(db, account.id) == 1

            await record_current_location(
                db,
                account_id=account.id,
                device_id=device.id,
                sample=LocationSample(
                    latitude=40.0,
                    longitude=-75.0,
                    observed_at=now,
                    horizontal_accuracy_m=10,
                    heading_deg=90,
                    speed_mps=5,
                    client_sequence=1,
                    consent_policy_version=policy.version,
                ),
                policy=policy,
                now=now,
            )

            revoked = await set_foreground_location_consent(
                db,
                account_id=account.id,
                device_id=device.id,
                platform=device.platform,
                decision="revoked",
                requested_policy_version=policy.version,
                requested_disclosure_version=settings.location_disclosure_version,
                current_policy_version=policy.version,
                current_disclosure_version=settings.location_disclosure_version,
                now=now,
            )
            assert revoked.decision == "revoked"
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(CurrentLocation)
                    .where(CurrentLocation.account_id == account.id)
                )
                == 0
            )
            assert await _consent_count(db, account.id) == 2

            replayed_revoke = await set_foreground_location_consent(
                db,
                account_id=account.id,
                device_id=device.id,
                platform=device.platform,
                decision="revoked",
                requested_policy_version=policy.version,
                requested_disclosure_version=settings.location_disclosure_version,
                current_policy_version=policy.version,
                current_disclosure_version=settings.location_disclosure_version,
                now=now,
            )
            assert replayed_revoke == revoked
            assert await _consent_count(db, account.id) == 2

            with pytest.raises(LocationConsentError) as stale:
                await set_foreground_location_consent(
                    db,
                    account_id=account.id,
                    device_id=device.id,
                    platform=device.platform,
                    decision="granted",
                    requested_policy_version="old-policy",
                    requested_disclosure_version=settings.location_disclosure_version,
                    current_policy_version=policy.version,
                    current_disclosure_version=settings.location_disclosure_version,
                    now=now,
                )
            assert stale.value.code == "LOCATION_POLICY_MISMATCH"
            assert await _consent_count(db, account.id) == 2

            await db.execute(delete(Account).where(Account.id == account.id))
            await db.commit()
    finally:
        await engine.dispose()


async def _consent_count(db: AsyncSession, account_id: uuid.UUID) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(LocationConsentEvent)
            .where(LocationConsentEvent.account_id == account_id)
        )
    )
