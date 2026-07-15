import asyncio
import os
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from geoalchemy2 import WKTElement
from geoalchemy2.elements import WKBElement
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, CurrentLocation, Device, LocationConsentEvent


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_location_persistence_is_current_only_indexed_and_cascading() -> None:
    asyncio.run(_location_persistence())


async def _location_persistence() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    account = Account()
    device = Device(
        account=account,
        platform="ios",
        installation_id=f"location-test-{now.timestamp()}",
    )

    try:
        async with factory() as db:
            db.add_all([account, device])
            await db.flush()
            account_id = account.id
            device_id = device.id
            db.add(
                LocationConsentEvent(
                    account_id=account_id,
                    device_id=device_id,
                    policy_version="location-v1",
                    disclosure_version="location-disclosure-v1",
                    platform="ios",
                    decision="granted",
                    decided_at=now,
                )
            )
            db.add(
                CurrentLocation(
                    account_id=account_id,
                    source_device_id=device_id,
                    position=cast(WKBElement, WKTElement("POINT(-75 40)", srid=4326)),
                    observed_at=now,
                    received_at=now,
                    horizontal_accuracy_m=8.0,
                    heading_deg=45.0,
                    speed_mps=3.0,
                    client_sequence=1,
                    expires_at=now + timedelta(minutes=2),
                    consent_policy_version="location-v1",
                    quality_state="usable",
                    version=1,
                )
            )
            await db.commit()

            stored = await db.scalar(
                select(CurrentLocation).where(CurrentLocation.account_id == account_id)
            )
            assert stored is not None
            assert stored.position.srid == 4326
            assert (
                await db.scalar(
                    select(func.ST_AsText(CurrentLocation.position)).where(
                        CurrentLocation.account_id == account_id
                    )
                )
                == "POINT(-75 40)"
            )

            duplicate = CurrentLocation(
                account_id=account_id,
                source_device_id=device_id,
                position=cast(WKBElement, WKTElement("POINT(-74 41)", srid=4326)),
                observed_at=now + timedelta(seconds=1),
                received_at=now + timedelta(seconds=1),
                horizontal_accuracy_m=8.0,
                client_sequence=2,
                expires_at=now + timedelta(minutes=2),
                consent_policy_version="location-v1",
                quality_state="usable",
                version=2,
            )
            db.add(duplicate)
            with pytest.raises(IntegrityError):
                await db.commit()
            await db.rollback()

            index_method = await db.scalar(
                text(
                    "SELECT am.amname FROM pg_class i "
                    "JOIN pg_am am ON am.oid = i.relam "
                    "WHERE i.relname = 'ix_current_location_position'"
                )
            )
            assert index_method == "gist"

            await db.execute(delete(Account).where(Account.id == account_id))
            await db.commit()
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(CurrentLocation)
                    .where(CurrentLocation.account_id == account_id)
                )
                == 0
            )
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(LocationConsentEvent)
                    .where(LocationConsentEvent.account_id == account_id)
                )
                == 0
            )
    finally:
        await engine.dispose()
