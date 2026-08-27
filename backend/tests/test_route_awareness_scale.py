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
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.channels.constants import GENERAL_CHANNEL_ID
from app.config import Settings
from app.db.models import (
    Account,
    AccountRouteMode,
    Channel,
    ChannelSelection,
    CurrentLocation,
    Device,
    LocationConsentEvent,
    MediaGrant,
    Session,
)
from app.ptt.provider import FakeMediaProvider
from app.ptt.proximity import find_eligible_receive_grants, proximity_policy_from_settings
from app.ptt.service import reconcile_proximity_delivery
from app.route_context.models import CurrentRouteContext

TARGET_MS = 400
CORRIDOR_A = "a" * 64
CORRIDOR_B = "b" * 64
CORRIDOR_C = "c" * 64


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_route_awareness_control_plane_at_100_25_10_scale() -> None:
    asyncio.run(_exercise_scale())


async def _exercise_scale() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 8, 27, 2, 30, tzinfo=UTC)

    receiver_indexes = tuple(range(25))
    nearby_publisher_indexes = (40, 41, 42, 43, 44)
    same_road_publisher_indexes = (45, 46, 47, 48)
    denied_publisher_index = 49
    publisher_indexes = (
        nearby_publisher_indexes + same_road_publisher_indexes + (denied_publisher_index,)
    )

    accounts = [
        Account(
            channel_selection=ChannelSelection(channel_id=GENERAL_CHANNEL_ID),
            route_mode=AccountRouteMode(
                mode="same_road" if index >= 45 and index <= 49 else "nearby",
                selected_at=now,
            ),
        )
        for index in range(100)
    ]
    devices = [
        Device(
            account=account,
            platform="ios" if index % 2 == 0 else "android",
            installation_id=f"route-scale-{index:03d}-{uuid.uuid4()}",
        )
        for index, account in enumerate(accounts)
    ]
    cleanup_account_ids: list[uuid.UUID] = []

    try:
        async with factory() as db:
            db.add_all(accounts)
            await db.flush()
            cleanup_account_ids = [account.id for account in accounts]

            channel = await db.scalar(select(Channel).where(Channel.id == GENERAL_CHANNEL_ID))
            assert channel is not None
            room_ref = channel.provider_room_ref

            for index, (account, device) in enumerate(zip(accounts, devices, strict=True)):
                db.add_all(
                    [
                        Session(
                            account_id=account.id,
                            device_id=device.id,
                            refresh_token_hash=f"s07-scale-refresh-{uuid.uuid4()}",
                            expires_at=(now + timedelta(minutes=10)).replace(tzinfo=None),
                        ),
                        LocationConsentEvent(
                            account_id=account.id,
                            device_id=device.id,
                            policy_version=settings.location_policy_version,
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
                                WKTElement(f"POINT({index * 0.000001} 0)", srid=4326),
                            ),
                            observed_at=now,
                            received_at=now,
                            horizontal_accuracy_m=10,
                            client_sequence=1,
                            expires_at=now + timedelta(minutes=2),
                            consent_policy_version=settings.location_policy_version,
                            quality_state="usable",
                            version=1,
                        ),
                    ]
                )
            await db.flush()

            for index in (*receiver_indexes, *same_road_publisher_indexes, denied_publisher_index):
                if index <= 19:
                    corridor = CORRIDOR_A
                    direction = "north" if index % 2 == 0 else "northeast"
                elif index <= 21:
                    corridor = CORRIDOR_B
                    direction = "north"
                elif index <= 24:
                    corridor = CORRIDOR_A
                    direction = "south"
                elif index == denied_publisher_index:
                    corridor = CORRIDOR_C
                    direction = "north"
                else:
                    corridor = CORRIDOR_A
                    direction = "north"
                db.add(
                    CurrentRouteContext(
                        account_id=accounts[index].id,
                        corridor_digest=corridor,
                        direction=direction,
                        confidence="confident",
                        source_location_version=1,
                        provider_version="fake-v1",
                        policy_version=settings.route_context_policy_version,
                        matched_at=now,
                        expires_at=now + timedelta(seconds=90),
                        version=1,
                    )
                )

            for index in receiver_indexes:
                db.add(
                    MediaGrant(
                        account_id=accounts[index].id,
                        device_id=devices[index].id,
                        channel_id=GENERAL_CHANNEL_ID,
                        grant_kind="receive",
                        provider="livekit",
                        provider_room_ref=room_ref,
                        provider_participant_ref=f"s07_receiver_{index:03d}",
                        action_scope="subscribe",
                        policy_version=settings.ptt_policy_version,
                        idempotency_key_hash=f"{index:064x}",
                        request_fingerprint=f"{index + 100:064x}",
                        issued_at=now,
                        expires_at=now + timedelta(minutes=5),
                        outcome_code="issued",
                    )
                )

            for index in publisher_indexes:
                parent = MediaGrant(
                    account_id=accounts[index].id,
                    device_id=devices[index].id,
                    channel_id=GENERAL_CHANNEL_ID,
                    grant_kind="receive",
                    provider="livekit",
                    provider_room_ref=room_ref,
                    provider_participant_ref=f"s07_publisher_{index:03d}",
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
                        account_id=accounts[index].id,
                        device_id=devices[index].id,
                        channel_id=GENERAL_CHANNEL_ID,
                        parent_grant_id=parent.id,
                        grant_kind="transmit",
                        provider="livekit",
                        provider_room_ref=room_ref,
                        provider_participant_ref=f"s07_publisher_{index:03d}",
                        provider_track_ref=f"s07_track_{index:03d}",
                        action_scope="microphone_publish",
                        policy_version=settings.ptt_policy_version,
                        proximity_policy_version=settings.ptt_proximity_policy_version,
                        eligibility_evaluated_at=now,
                        idempotency_key_hash=f"{index + 400:064x}",
                        request_fingerprint=f"{index + 500:064x}",
                        issued_at=now,
                        expires_at=now + timedelta(seconds=30),
                        outcome_code="delivery_ready",
                    )
                )
            await db.commit()

            policy = proximity_policy_from_settings(
                settings,
                channel_id=GENERAL_CHANNEL_ID,
                room_ref=room_ref,
            )

            nearby_ms: list[float] = []
            for index in nearby_publisher_indexes:
                started = perf_counter()
                result = await find_eligible_receive_grants(
                    db,
                    sender_account_id=accounts[index].id,
                    sender_device_id=devices[index].id,
                    policy=policy,
                    now=now,
                )
                nearby_ms.append((perf_counter() - started) * 1_000)
                assert len(result) == 25

            same_road_ms: list[float] = []
            for index in same_road_publisher_indexes:
                started = perf_counter()
                result = await find_eligible_receive_grants(
                    db,
                    sender_account_id=accounts[index].id,
                    sender_device_id=devices[index].id,
                    policy=policy,
                    now=now,
                )
                same_road_ms.append((perf_counter() - started) * 1_000)
                assert len(result) == 20

            denied_ms: list[float] = []
            for _ in range(5):
                started = perf_counter()
                result = await find_eligible_receive_grants(
                    db,
                    sender_account_id=accounts[denied_publisher_index].id,
                    sender_device_id=devices[denied_publisher_index].id,
                    policy=policy,
                    now=now,
                )
                denied_ms.append((perf_counter() - started) * 1_000)
                assert result == ()

            started = perf_counter()
            receipt = await reconcile_proximity_delivery(
                db,
                provider=FakeMediaProvider(),
                settings=settings,
                now=now,
            )
            reconciliation_ms = [(perf_counter() - started) * 1_000]
            assert receipt.transmissions_examined == 10

            metrics = {
                "registered_accounts": 100,
                "connected_receivers": 25,
                "active_publishers": 10,
                "nearby_publishers": 5,
                "same_road_publishers": 5,
                "same_corridor_compatible_receivers": 20,
                "same_road_denied_receivers": 5,
                "nearby_eligible_p95_ms": round(_p95(nearby_ms), 2),
                "same_road_eligible_p95_ms": round(_p95(same_road_ms), 2),
                "same_road_zero_recipient_p95_ms": round(_p95(denied_ms), 2),
                "reconciliation_p95_ms": round(_p95(reconciliation_ms), 2),
                "target_ms": TARGET_MS,
            }
            print("Route-awareness synthetic scale: " + json.dumps(metrics, sort_keys=True))
            assert all(
                value <= TARGET_MS for key, value in metrics.items() if key.endswith("_p95_ms")
            )
    finally:
        if cleanup_account_ids:
            async with factory() as db:
                await db.execute(delete(Account).where(Account.id.in_(cleanup_account_ids)))
                await db.commit()
        await engine.dispose()
