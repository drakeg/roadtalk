import asyncio
import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from math import ceil
from time import perf_counter

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.channels.constants import GENERAL_CHANNEL_ID
from app.config import Settings
from app.db.models import (
    Account,
    ChannelSelection,
    Device,
    Notification,
    NotificationPreferences,
    Session,
)
from app.notifications.contracts import UrgentAlertNotificationPayload
from app.notifications.service import compose_authorized_notifications
from app.ptt.proximity import EligibleReceiveGrant

# Locked before the named S09-D09 evidence run. This covers the whole server-side
# authorization + preference narrowing + persistence path for one alert publisher.
TARGET_P95_MS = 1_500
REGISTERED_ACCOUNTS = 100
POTENTIAL_RECIPIENTS = 25
ALERT_PUBLISHERS = 10
OPTED_OUT_RECIPIENTS = 5


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_notification_composition_at_100_25_10_scale() -> None:
    asyncio.run(_exercise_scale())


async def _exercise_scale() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 9, 3, 18, tzinfo=UTC)
    session_now = now.replace(tzinfo=None)

    accounts = [Account(account_type="registered") for _ in range(REGISTERED_ACCOUNTS)]
    recipient_indexes = tuple(range(POTENTIAL_RECIPIENTS))
    publisher_indexes = tuple(
        range(REGISTERED_ACCOUNTS - ALERT_PUBLISHERS, REGISTERED_ACCOUNTS)
    )
    cleanup_account_ids: list[uuid.UUID] = []

    try:
        async with factory() as db:
            db.add_all(accounts)
            await db.flush()
            cleanup_account_ids = [account.id for account in accounts]

            for index in recipient_indexes[-OPTED_OUT_RECIPIENTS:]:
                db.add(
                    NotificationPreferences(
                        account_id=accounts[index].id,
                        urgent_alert_enabled=False,
                        channel_activity_enabled=True,
                    )
                )

            publisher_devices: dict[int, Device] = {}
            for index in publisher_indexes:
                account = accounts[index]
                device = Device(
                    account_id=account.id,
                    platform="ios" if index % 2 == 0 else "android",
                    installation_id=f"notification-scale-{index:03d}-{uuid.uuid4().hex}",
                    last_seen_at=session_now,
                )
                db.add(device)
                await db.flush()
                publisher_devices[index] = device
                db.add_all(
                    (
                        Session(
                            account_id=account.id,
                            device_id=device.id,
                            refresh_token_hash=uuid.uuid4().hex + uuid.uuid4().hex,
                            expires_at=session_now + timedelta(hours=1),
                        ),
                        ChannelSelection(
                            account_id=account.id,
                            channel_id=GENERAL_CHANNEL_ID,
                        ),
                    )
                )
            await db.commit()

            potential = tuple(
                EligibleReceiveGrant(
                    receive_grant_id=uuid.uuid4(),
                    account_id=accounts[index].id,
                    device_id=uuid.uuid4(),
                    participant_ref=f"notification-scale-recipient-{index:03d}",
                )
                for index in recipient_indexes
            )

            async def eligible_subset(
                *args: object, **kwargs: object
            ) -> tuple[EligibleReceiveGrant, ...]:
                del args, kwargs
                return potential

            compose_ms: list[float] = []
            recipient_counts: list[int] = []
            for sequence, index in enumerate(publisher_indexes):
                payload = UrgentAlertNotificationPayload(
                    message=f"Synthetic D09 alert {sequence + 1}.",
                    issued_at=now + timedelta(seconds=sequence),
                    expires_at=now + timedelta(minutes=5),
                )
                started = perf_counter()
                receipts = await compose_authorized_notifications(
                    db,
                    sender_account_id=accounts[index].id,
                    sender_device_id=publisher_devices[index].id,
                    payload=payload,
                    idempotency_key=f"s09-d09-scale-alert-{sequence:02d}",
                    settings=settings,
                    now=now + timedelta(seconds=sequence),
                    eligibility_finder=eligible_subset,
                )
                compose_ms.append((perf_counter() - started) * 1_000)
                recipient_counts.append(len(receipts))

            expected_recipients = POTENTIAL_RECIPIENTS - OPTED_OUT_RECIPIENTS
            assert recipient_counts == [expected_recipients] * ALERT_PUBLISHERS
            stored = await db.scalar(select(func.count()).select_from(Notification))
            assert stored == expected_recipients * ALERT_PUBLISHERS

            p95_ms = round(_p95(compose_ms), 2)
            metrics = {
                "registered_accounts": REGISTERED_ACCOUNTS,
                "potential_recipients": POTENTIAL_RECIPIENTS,
                "alert_publishers": ALERT_PUBLISHERS,
                "opted_out_recipients": OPTED_OUT_RECIPIENTS,
                "delivered_recipients_per_alert": expected_recipients,
                "compose_p95_ms": p95_ms,
                "target_p95_ms": TARGET_P95_MS,
                "external_push_provider": "disabled",
                "incremental_recurring_cost_usd": 0,
            }
            print(
                "Notification synthetic scale: "
                + json.dumps(metrics, sort_keys=True)
            )
            assert p95_ms <= TARGET_P95_MS
    finally:
        if cleanup_account_ids:
            async with factory() as db:
                await db.execute(delete(Account).where(Account.id.in_(cleanup_account_ids)))
                await db.commit()
        await engine.dispose()
