import asyncio
import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from math import ceil
from time import perf_counter
from typing import cast

import pytest
from geoalchemy2 import WKTElement
from geoalchemy2.elements import WKBElement
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, CurrentLocation, Device, LocationConsentEvent, Session
from app.presence.lifecycle import current_presence_snapshot

TARGET_MS = 400
ACCOUNT_COUNT = 100
VIEWER_COUNT = 25
PUBLISHER_COUNT = 10
REFRESH_ROUNDS = 5


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_presence_at_100_25_10_scale() -> None:
    asyncio.run(_exercise_scale())


async def _exercise_scale() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 8, 29, 4, 0, tzinfo=UTC)
    accounts = [Account(account_type="registered") for _ in range(ACCOUNT_COUNT)]
    cleanup_account_ids: list[uuid.UUID] = []

    try:
        async with factory() as db:
            db.add_all(accounts)
            await db.flush()
            cleanup_account_ids = [account.id for account in accounts]

            publishers = accounts[VIEWER_COUNT : VIEWER_COUNT + PUBLISHER_COUNT]
            for index, account in enumerate(publishers):
                device = Device(
                    account=account,
                    platform="ios" if index % 2 == 0 else "android",
                    installation_id=f"s08-presence-scale-{index:03d}-{uuid.uuid4()}",
                    last_seen_at=now,
                )
                db.add(device)
                await db.flush()
                db.add_all(
                    [
                        Session(
                            account_id=account.id,
                            device_id=device.id,
                            refresh_token_hash=f"s08-presence-refresh-{uuid.uuid4()}",
                            expires_at=(now + timedelta(minutes=10)).replace(tzinfo=None),
                        ),
                        LocationConsentEvent(
                            account_id=account.id,
                            device_id=device.id,
                            policy_version=settings.location_policy_version,
                            disclosure_version=settings.location_disclosure_version,
                            platform=device.platform,
                            decision="granted",
                            decided_at=now,
                        ),
                        CurrentLocation(
                            account_id=account.id,
                            source_device_id=device.id,
                            position=cast(
                                WKBElement,
                                WKTElement(
                                    f"POINT({-75.00020 + index * 0.00001} 40.00000)",
                                    srid=4326,
                                ),
                            ),
                            observed_at=now,
                            received_at=now,
                            horizontal_accuracy_m=10.0,
                            client_sequence=1,
                            expires_at=now + timedelta(minutes=2),
                            consent_policy_version=settings.location_policy_version,
                            quality_state="usable",
                            version=1,
                        ),
                    ]
                )
            await db.commit()

            lookup_ms: list[float] = []
            for viewer in accounts[:VIEWER_COUNT]:
                started = perf_counter()
                snapshot = await current_presence_snapshot(
                    db,
                    viewer_account_id=viewer.id,
                    location_policy_version=settings.location_policy_version,
                    now=now,
                )
                lookup_ms.append((perf_counter() - started) * 1_000)
                assert len(snapshot.cells) == 1
                assert snapshot.cells[0].account_count == PUBLISHER_COUNT

            refresh_ms: list[float] = []
            for round_index in range(REFRESH_ROUNDS):
                refreshed_at = now + timedelta(seconds=round_index + 1)
                for viewer in accounts[:VIEWER_COUNT]:
                    started = perf_counter()
                    snapshot = await current_presence_snapshot(
                        db,
                        viewer_account_id=viewer.id,
                        location_policy_version=settings.location_policy_version,
                        now=refreshed_at,
                    )
                    refresh_ms.append((perf_counter() - started) * 1_000)
                    assert len(snapshot.cells) == 1
                    assert snapshot.cells[0].account_count == PUBLISHER_COUNT

            metrics = {
                "registered_accounts": ACCOUNT_COUNT,
                "presence_viewers": VIEWER_COUNT,
                "active_publishers": PUBLISHER_COUNT,
                "refresh_rounds": REFRESH_ROUNDS,
                "lookup_aggregation_p95_ms": round(_p95(lookup_ms), 2),
                "refresh_p95_ms": round(_p95(refresh_ms), 2),
                "target_ms": TARGET_MS,
            }
            print("Presence synthetic scale: " + json.dumps(metrics, sort_keys=True))
            assert metrics["lookup_aggregation_p95_ms"] <= TARGET_MS
            assert metrics["refresh_p95_ms"] <= TARGET_MS
    finally:
        if cleanup_account_ids:
            async with factory() as db:
                await db.execute(delete(Account).where(Account.id.in_(cleanup_account_ids)))
                await db.commit()
        await engine.dispose()
