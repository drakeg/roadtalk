import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from geoalchemy2 import WKTElement
from geoalchemy2.elements import WKBElement
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, CurrentLocation, Device, LocationConsentEvent, Session
from app.presence.lifecycle import current_presence_snapshot


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_presence_is_current_only_and_lifecycle_gated() -> None:
    asyncio.run(_presence_lifecycle())


async def _presence_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    viewer_id = uuid.uuid4()
    visible_ids: list[uuid.UUID] = []

    try:
        async with factory() as db:
            viewer = Account(id=viewer_id)
            db.add(viewer)
            for index in range(3):
                account = Account()
                device = Device(
                    account=account,
                    platform="ios",
                    installation_id=f"presence-lifecycle-{uuid.uuid4()}",
                )
                db.add_all([account, device])
                await db.flush()
                visible_ids.append(account.id)
                db.add(
                    Session(
                        account_id=account.id,
                        device_id=device.id,
                        refresh_token_hash=f"presence-refresh-{uuid.uuid4()}",
                        expires_at=now + timedelta(hours=1),
                    )
                )
                db.add(
                    LocationConsentEvent(
                        account_id=account.id,
                        device_id=device.id,
                        policy_version="location-v1",
                        disclosure_version="location-disclosure-v1",
                        platform="ios",
                        decision="granted",
                        decided_at=now,
                    )
                )
                db.add(
                    CurrentLocation(
                        account_id=account.id,
                        source_device_id=device.id,
                        position=cast(
                            WKBElement,
                            WKTElement(f"POINT({-75.0001 + index * 0.0001} 40.0)", srid=4326),
                        ),
                        observed_at=now,
                        received_at=now,
                        horizontal_accuracy_m=10.0,
                        client_sequence=1,
                        expires_at=now + timedelta(seconds=120),
                        consent_policy_version="location-v1",
                        quality_state="usable",
                        version=1,
                    )
                )
            await db.commit()

            visible = await current_presence_snapshot(
                db,
                viewer_account_id=viewer_id,
                location_policy_version="location-v1",
                now=now,
            )
            assert len(visible.cells) == 1
            assert visible.cells[0].account_count == 3

            await db.execute(
                update(Session)
                .where(Session.account_id == visible_ids[0])
                .values(revoked_at=now, revoke_reason="test")
            )
            await db.commit()
            after_logout = await current_presence_snapshot(
                db,
                viewer_account_id=viewer_id,
                location_policy_version="location-v1",
                now=now,
            )
            assert after_logout.cells == ()

            source_device = await db.scalar(
                select(Device.id).where(Device.account_id == visible_ids[1])
            )
            assert source_device is not None
            db.add(
                LocationConsentEvent(
                    account_id=visible_ids[1],
                    device_id=source_device,
                    policy_version="location-v1",
                    disclosure_version="location-disclosure-v1",
                    platform="ios",
                    decision="revoked",
                    decided_at=now + timedelta(seconds=1),
                )
            )
            await db.commit()
            after_withdrawal = await current_presence_snapshot(
                db,
                viewer_account_id=viewer_id,
                location_policy_version="location-v1",
                now=now + timedelta(seconds=1),
            )
            assert after_withdrawal.cells == ()

            await db.execute(
                update(CurrentLocation)
                .where(CurrentLocation.account_id == visible_ids[2])
                .values(expires_at=now + timedelta(seconds=2))
            )
            await db.commit()
            stale = await current_presence_snapshot(
                db,
                viewer_account_id=viewer_id,
                location_policy_version="location-v1",
                now=now + timedelta(seconds=3),
            )
            assert stale.cells == ()
    finally:
        await engine.dispose()
