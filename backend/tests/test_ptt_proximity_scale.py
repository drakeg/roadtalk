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
from app.db.models import (
    Account,
    CurrentLocation,
    Device,
    LocationConsentEvent,
    MediaGrant,
    Session,
)
from app.ptt.provider import FakeMediaProvider
from app.ptt.proximity import (
    ProximityEligibilityError,
    find_eligible_receive_grants,
    proximity_policy_from_settings,
)
from app.ptt.service import reconcile_proximity_delivery

TARGET_MS = 400


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_proximity_control_plane_at_100_25_10_scale() -> None:
    asyncio.run(_exercise_scale())


async def _exercise_scale() -> None:
    """Measure private proximity decisions on migrated PostGIS with deterministic fakes."""
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 8, 13, 4, tzinfo=UTC)
    accounts = [Account() for _ in range(100)]
    devices = [
        Device(
            account=account,
            platform="ios" if index % 2 == 0 else "android",
            installation_id=f"proximity-scale-{index:03d}-{uuid.uuid4()}",
        )
        for index, account in enumerate(accounts)
    ]
    account_ids: list[uuid.UUID] = []

    try:
        async with factory() as db:
            db.add_all(accounts)
            await db.flush()
            account_ids = [account.id for account in accounts]

            for index, (account, device) in enumerate(zip(accounts, devices, strict=True)):
                # Receivers and eight publishers are nearby. Publisher 8 is far enough
                # for an empty audience; publisher 9 is degraded for a denied decision.
                longitude = 1.0 if index == 33 else index * 0.00001
                quality = "degraded" if index == 34 else "usable"
                db.add_all(
                    [
                        Session(
                            account_id=account.id,
                            device_id=device.id,
                            refresh_token_hash=f"scale-refresh-{uuid.uuid4()}",
                            expires_at=(now + timedelta(minutes=10)).replace(tzinfo=None),
                        ),
                        LocationConsentEvent(
                            account_id=account.id,
                            device_id=device.id,
                            policy_version="location-v1",
                            disclosure_version="location-disclosure-v1",
                            platform=device.platform,
                            decision="granted",
                            decided_at=now,
                        ),
                        CurrentLocation(
                            account_id=account.id,
                            source_device_id=device.id,
                            position=cast(
                                WKBElement,
                                WKTElement(f"POINT({longitude} 0)", srid=4326),
                            ),
                            observed_at=now,
                            received_at=now,
                            horizontal_accuracy_m=10,
                            client_sequence=1,
                            expires_at=now + timedelta(minutes=2),
                            consent_policy_version="location-v1",
                            quality_state=quality,
                            version=1,
                        ),
                    ]
                )
                if index < 25:
                    db.add(
                        MediaGrant(
                            account_id=account.id,
                            device_id=device.id,
                            grant_kind="receive",
                            provider="livekit",
                            provider_room_ref=settings.ptt_controlled_room_ref,
                            provider_participant_ref=f"receiver_{index:03d}",
                            action_scope="subscribe",
                            policy_version=settings.ptt_policy_version,
                            idempotency_key_hash=f"{index:064x}",
                            request_fingerprint=f"{index + 100:064x}",
                            issued_at=now,
                            expires_at=now + timedelta(minutes=5),
                            outcome_code="issued",
                        )
                    )
                elif index < 35:
                    parent = MediaGrant(
                        account_id=account.id,
                        device_id=device.id,
                        grant_kind="receive",
                        provider="livekit",
                        provider_room_ref=settings.ptt_controlled_room_ref,
                        provider_participant_ref=f"publisher_{index - 25:03d}",
                        action_scope="subscribe",
                        policy_version=settings.ptt_policy_version,
                        idempotency_key_hash=f"{index + 200:064x}",
                        request_fingerprint=f"{index + 300:064x}",
                        issued_at=now,
                        expires_at=now + timedelta(minutes=5),
                        revoked_at=now,
                        outcome_code="replaced_by_synthetic_publish",
                    )
                    db.add(parent)
                    await db.flush()
                    db.add(
                        MediaGrant(
                            account_id=account.id,
                            device_id=device.id,
                            parent_grant_id=parent.id,
                            grant_kind="transmit",
                            provider="livekit",
                            provider_room_ref=settings.ptt_controlled_room_ref,
                            provider_participant_ref=f"publisher_{index - 25:03d}",
                            provider_track_ref=f"track_{index - 25:03d}",
                            action_scope="microphone_publish",
                            policy_version=settings.ptt_policy_version,
                            proximity_policy_version=settings.ptt_proximity_policy_version,
                            eligibility_evaluated_at=now,
                            idempotency_key_hash=f"{index:064x}",
                            request_fingerprint=f"{index + 100:064x}",
                            issued_at=now,
                            expires_at=now + timedelta(seconds=30),
                            outcome_code="delivery_ready",
                        )
                    )
            await db.commit()

            policy = proximity_policy_from_settings(settings)
            eligible_ms: list[float] = []
            for index in range(25, 33):
                started = perf_counter()
                result = await find_eligible_receive_grants(
                    db,
                    sender_account_id=accounts[index].id,
                    sender_device_id=devices[index].id,
                    policy=policy,
                    now=now,
                )
                eligible_ms.append((perf_counter() - started) * 1_000)
                assert len(result) == 25

            empty_ms: list[float] = []
            for _ in range(5):
                started = perf_counter()
                result = await find_eligible_receive_grants(
                    db,
                    sender_account_id=accounts[33].id,
                    sender_device_id=devices[33].id,
                    policy=policy,
                    now=now,
                )
                empty_ms.append((perf_counter() - started) * 1_000)
                assert result == ()

            denied_ms: list[float] = []
            for _ in range(5):
                started = perf_counter()
                with pytest.raises(ProximityEligibilityError):
                    await find_eligible_receive_grants(
                        db,
                        sender_account_id=accounts[34].id,
                        sender_device_id=devices[34].id,
                        policy=policy,
                        now=now,
                    )
                denied_ms.append((perf_counter() - started) * 1_000)

            started = perf_counter()
            receipt = await reconcile_proximity_delivery(
                db,
                provider=FakeMediaProvider(),
                settings=settings,
                now=now,
            )
            reconciliation_ms = [(perf_counter() - started) * 1_000]
            assert receipt.transmissions_examined == 10
            assert receipt.transmissions_ready == 8
            assert receipt.transmissions_ended == 1
            assert receipt.transmissions_pending == 1

            metrics = {
                "registered_accounts": 100,
                "connected_receivers": 25,
                "active_publishers": 10,
                "eligible_p95_ms": round(_p95(eligible_ms), 2),
                "denied_p95_ms": round(_p95(denied_ms), 2),
                "empty_audience_p95_ms": round(_p95(empty_ms), 2),
                "reconciliation_p95_ms": round(_p95(reconciliation_ms), 2),
                "target_ms": TARGET_MS,
            }
            print("Proximity synthetic scale: " + json.dumps(metrics, sort_keys=True))
            assert all(
                value <= TARGET_MS for key, value in metrics.items() if key.endswith("_p95_ms")
            )
    finally:
        if account_ids:
            async with factory() as db:
                await db.execute(delete(Account).where(Account.id.in_(account_ids)))
                await db.commit()
        await engine.dispose()
