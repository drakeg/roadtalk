import asyncio
import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, AccountRouteMode, Device, LocationConsentEvent
from app.location.quality import LocationSample, policy_from_settings
from app.location.service import delete_current_location, record_current_location
from app.route_context.lifecycle import corridor_digest, refresh_current_route_context
from app.route_context.models import CurrentRouteContext
from app.route_context.provider import (
    FakeRouteContextFixture,
    FakeRouteContextProvider,
    RouteContextConfidence,
    RouteContextDirection,
)


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_current_route_context_replacement_replay_and_cleanup() -> None:
    asyncio.run(_route_context_lifecycle())


async def _route_context_lifecycle() -> None:
    settings = Settings(environment="test", route_context_provider="fake")
    policy = policy_from_settings(settings)
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    account = Account()
    device = Device(
        account=account,
        platform="ios",
        installation_id=f"route-context-{now.timestamp()}",
    )

    try:
        async with factory() as db:
            db.add_all([account, device])
            await db.flush()
            db.add_all(
                [
                    LocationConsentEvent(
                        account_id=account.id,
                        device_id=device.id,
                        policy_version=policy.version,
                        disclosure_version="location-disclosure-v1",
                        platform="ios",
                        decision="granted",
                        decided_at=now,
                    ),
                    AccountRouteMode(
                        account_id=account.id,
                        mode="same_road",
                        selected_at=now,
                        version=1,
                    ),
                ]
            )
            await db.commit()

            first = await record_current_location(
                db,
                account_id=account.id,
                device_id=device.id,
                sample=LocationSample(
                    latitude=40.12345,
                    longitude=-76.54321,
                    observed_at=now,
                    horizontal_accuracy_m=10,
                    heading_deg=90,
                    speed_mps=20,
                    client_sequence=1,
                    consent_policy_version=policy.version,
                ),
                policy=policy,
                now=now,
            )
            assert first.version == 1

            raw_corridor = "provider-road-segment-17"
            provider = FakeRouteContextProvider(
                {
                    (40.12345, -76.54321): FakeRouteContextFixture(
                        provider_corridor_ref=raw_corridor,
                        direction=RouteContextDirection.EAST,
                    )
                },
                clock=lambda: now + timedelta(seconds=1),
            )
            receipt = await refresh_current_route_context(
                db,
                account_id=account.id,
                provider=provider,
                settings=settings,
                now=now + timedelta(seconds=1),
            )
            assert receipt.available is True
            assert receipt.source_location_version == 1
            assert receipt.version == 1

            stored = await db.scalar(
                select(CurrentRouteContext).where(CurrentRouteContext.account_id == account.id)
            )
            assert stored is not None
            assert stored.corridor_digest != raw_corridor
            assert raw_corridor not in stored.corridor_digest
            assert stored.corridor_digest == corridor_digest(
                secret=settings.token_signing_key.get_secret_value(),
                provider_version="fake-v1",
                provider_corridor_ref=raw_corridor,
            )
            assert stored.direction == "east"
            assert stored.confidence == "confident"

            replay = await refresh_current_route_context(
                db,
                account_id=account.id,
                provider=provider,
                settings=settings,
                now=now + timedelta(seconds=1),
            )
            assert replay.version == 1

            second_time = now + timedelta(seconds=3)
            second = await record_current_location(
                db,
                account_id=account.id,
                device_id=device.id,
                sample=LocationSample(
                    latitude=40.12346,
                    longitude=-76.54321,
                    observed_at=second_time,
                    horizontal_accuracy_m=10,
                    heading_deg=90,
                    speed_mps=20,
                    client_sequence=2,
                    consent_policy_version=policy.version,
                ),
                policy=policy,
                now=second_time,
            )
            assert second.version == 2
            replacement_provider = FakeRouteContextProvider(
                {
                    (40.12346, -76.54321): FakeRouteContextFixture(
                        provider_corridor_ref="provider-road-segment-18",
                        direction=RouteContextDirection.EAST,
                    )
                },
                clock=lambda: second_time + timedelta(seconds=1),
            )
            replacement = await refresh_current_route_context(
                db,
                account_id=account.id,
                provider=replacement_provider,
                settings=settings,
                now=second_time + timedelta(seconds=1),
            )
            assert replacement.available is True
            assert replacement.source_location_version == 2
            assert replacement.version == 2

            ambiguous_provider = FakeRouteContextProvider(
                {
                    (40.12346, -76.54321): FakeRouteContextFixture(
                        provider_corridor_ref="provider-road-segment-18",
                        direction=RouteContextDirection.EAST,
                        confidence=RouteContextConfidence.AMBIGUOUS,
                    )
                },
                clock=lambda: second_time + timedelta(seconds=2),
            )
            unavailable = await refresh_current_route_context(
                db,
                account_id=account.id,
                provider=ambiguous_provider,
                settings=settings,
                now=second_time + timedelta(seconds=2),
            )
            assert unavailable.available is False
            assert await db.scalar(
                select(CurrentRouteContext).where(CurrentRouteContext.account_id == account.id)
            ) is None

            restored = await refresh_current_route_context(
                db,
                account_id=account.id,
                provider=replacement_provider,
                settings=settings,
                now=second_time + timedelta(seconds=1),
            )
            assert restored.available is True
            assert await delete_current_location(db, account_id=account.id) is True
            assert await db.scalar(
                select(CurrentRouteContext).where(CurrentRouteContext.account_id == account.id)
            ) is None
    finally:
        await engine.dispose()
