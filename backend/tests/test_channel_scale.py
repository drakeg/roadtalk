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

from app.channels.constants import GENERAL_CHANNEL_ID, RV_CHANNEL_ID
from app.channels.security import hash_invite, new_invite, verify_invite
from app.channels.service import select_channel
from app.config import Settings
from app.db.models import (
    Account,
    Channel,
    ChannelMembership,
    ChannelSelection,
    CurrentLocation,
    Device,
    LocationConsentEvent,
    MediaGrant,
    Session,
)
from app.ptt.proximity import (
    ProximityEligibilityError,
    find_eligible_receive_grants,
    proximity_policy_from_settings,
)
from app.ptt.provider import FakeMediaProvider
from app.ptt.service import reconcile_proximity_delivery

TARGET_MS = 400
PRIVATE_CHANNEL_ID = uuid.UUID("10000000-0000-4000-8000-000000000006")
PRIVATE_ROOM_REF = "rm_s06_scale_private"


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_channel_control_plane_at_100_25_10_scale() -> None:
    asyncio.run(_exercise_scale())


async def _exercise_scale() -> None:
    settings = Settings(environment="test", channel_invite_pepper="s06-scale-pepper")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 8, 18, 22, tzinfo=UTC)

    channel_ids = [
        GENERAL_CHANNEL_ID if index < 40 else RV_CHANNEL_ID if index < 80 else PRIVATE_CHANNEL_ID
        for index in range(100)
    ]
    accounts = [Account(channel_selection=ChannelSelection(channel_id=channel_ids[index])) for index in range(100)]
    devices = [
        Device(
            account=account,
            platform="ios" if index % 2 == 0 else "android",
            installation_id=f"channel-scale-{index:03d}-{uuid.uuid4()}",
        )
        for index, account in enumerate(accounts)
    ]
    cleanup_account_ids: list[uuid.UUID] = []

    receiver_indexes = tuple(range(0, 10)) + tuple(range(40, 50)) + tuple(range(80, 85))
    publisher_indexes = (25, 26, 27, 28, 50, 51, 52, 85, 86, 87)

    try:
        async with factory() as db:
            private_channel = Channel(
                id=PRIVATE_CHANNEL_ID,
                display_label="Synthetic Private",
                channel_type="private",
                enabled=True,
                creator=accounts[80],
                provider_room_ref=PRIVATE_ROOM_REF,
                policy_version="channel-v1",
                version=1,
            )
            db.add(private_channel)
            db.add_all(accounts)
            await db.flush()
            cleanup_account_ids = [account.id for account in accounts]
            db.add_all(
                ChannelMembership(account_id=accounts[index].id, channel_id=PRIVATE_CHANNEL_ID)
                for index in range(80, 100)
            )

            public_rooms = {
                GENERAL_CHANNEL_ID: settings.ptt_controlled_room_ref,
                RV_CHANNEL_ID: "rm_v1_rv",
                PRIVATE_CHANNEL_ID: PRIVATE_ROOM_REF,
            }

            for index, (account, device) in enumerate(zip(accounts, devices, strict=True)):
                db.add_all(
                    [
                        Session(
                            account_id=account.id,
                            device_id=device.id,
                            refresh_token_hash=f"s06-scale-refresh-{uuid.uuid4()}",
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
                            position=cast(WKBElement, WKTElement(f"POINT({index * 0.000001} 0)", srid=4326)),
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

                channel_id = channel_ids[index]
                room_ref = public_rooms[channel_id]
                if index in receiver_indexes:
                    db.add(
                        MediaGrant(
                            account_id=account.id,
                            device_id=device.id,
                            channel_id=channel_id,
                            grant_kind="receive",
                            provider="livekit",
                            provider_room_ref=room_ref,
                            provider_participant_ref=f"s06_receiver_{index:03d}",
                            action_scope="subscribe",
                            policy_version=settings.ptt_policy_version,
                            idempotency_key_hash=f"{index:064x}",
                            request_fingerprint=f"{index + 100:064x}",
                            issued_at=now,
                            expires_at=now + timedelta(minutes=5),
                            outcome_code="issued",
                        )
                    )
                if index in publisher_indexes:
                    parent = MediaGrant(
                        account_id=account.id,
                        device_id=device.id,
                        channel_id=channel_id,
                        grant_kind="receive",
                        provider="livekit",
                        provider_room_ref=room_ref,
                        provider_participant_ref=f"s06_publisher_{index:03d}",
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
                            channel_id=channel_id,
                            parent_grant_id=parent.id,
                            grant_kind="transmit",
                            provider="livekit",
                            provider_room_ref=room_ref,
                            provider_participant_ref=f"s06_publisher_{index:03d}",
                            provider_track_ref=f"s06_track_{index:03d}",
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

            eligible_ms: list[float] = []
            expected_receivers = {
                GENERAL_CHANNEL_ID: 10,
                RV_CHANNEL_ID: 10,
                PRIVATE_CHANNEL_ID: 5,
            }
            for index in publisher_indexes:
                channel_id = channel_ids[index]
                policy = proximity_policy_from_settings(
                    settings,
                    channel_id=channel_id,
                    room_ref=public_rooms[channel_id],
                )
                started = perf_counter()
                result = await find_eligible_receive_grants(
                    db,
                    sender_account_id=accounts[index].id,
                    sender_device_id=devices[index].id,
                    policy=policy,
                    now=now,
                )
                eligible_ms.append((perf_counter() - started) * 1_000)
                assert len(result) == expected_receivers[channel_id]
                assert {channel_ids[cleanup_account_ids.index(item.account_id)] for item in result} == {channel_id}

            cross_channel_denied_ms: list[float] = []
            wrong_policy = proximity_policy_from_settings(
                settings,
                channel_id=RV_CHANNEL_ID,
                room_ref=public_rooms[RV_CHANNEL_ID],
            )
            for _ in range(5):
                started = perf_counter()
                with pytest.raises(ProximityEligibilityError):
                    await find_eligible_receive_grants(
                        db,
                        sender_account_id=accounts[25].id,
                        sender_device_id=devices[25].id,
                        policy=wrong_policy,
                        now=now,
                    )
                cross_channel_denied_ms.append((perf_counter() - started) * 1_000)

            switch_ms: list[float] = []
            for target in (GENERAL_CHANNEL_ID, RV_CHANNEL_ID, GENERAL_CHANNEL_ID, RV_CHANNEL_ID, GENERAL_CHANNEL_ID):
                started = perf_counter()
                await select_channel(db, account_id=accounts[60].id, channel_id=target, now=now)
                switch_ms.append((perf_counter() - started) * 1_000)

            invite = new_invite()
            encoded = hash_invite(invite, settings.channel_invite_pepper.get_secret_value(), salt=b"0123456789abcdef")
            invite_verify_ms: list[float] = []
            for _ in range(5):
                started = perf_counter()
                assert verify_invite(invite, encoded, settings.channel_invite_pepper.get_secret_value())
                invite_verify_ms.append((perf_counter() - started) * 1_000)

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
                "general_receivers": 10,
                "rv_receivers": 10,
                "private_receivers": 5,
                "eligible_p95_ms": round(_p95(eligible_ms), 2),
                "cross_channel_denied_p95_ms": round(_p95(cross_channel_denied_ms), 2),
                "selection_switch_p95_ms": round(_p95(switch_ms), 2),
                "invite_verify_p95_ms": round(_p95(invite_verify_ms), 2),
                "reconciliation_p95_ms": round(_p95(reconciliation_ms), 2),
                "target_ms": TARGET_MS,
            }
            print("Channel synthetic scale: " + json.dumps(metrics, sort_keys=True))
            assert all(value <= TARGET_MS for key, value in metrics.items() if key.endswith("_p95_ms"))
    finally:
        if cleanup_account_ids:
            async with factory() as db:
                await db.execute(delete(Account).where(Account.id.in_(cleanup_account_ids)))
                await db.commit()
        await engine.dispose()
