import asyncio
import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta

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
from app.notifications.models import NotificationDeliveryReceipt
from app.notifications.service import NotificationError, compose_authorized_notifications
from app.ptt.proximity import EligibleReceiveGrant


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_notification_authorization_and_idempotency_lifecycle() -> None:
    asyncio.run(_authorization_lifecycle())


async def _authorization_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    session_now = now.replace(tzinfo=None)

    sender = Account(account_type="registered")
    allowed = Account(account_type="registered")
    denied = Account(account_type="registered")
    opted_out = Account(account_type="registered")

    sender_device = Device(
        account=sender,
        platform="web",
        installation_id=f"notification-sender-{uuid.uuid4().hex}",
        last_seen_at=session_now,
    )
    sender_session = Session(
        account=sender,
        device=sender_device,
        refresh_token_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        expires_at=session_now + timedelta(hours=1),
    )
    sender.channel_selection = ChannelSelection(channel_id=GENERAL_CHANNEL_ID)
    opted_out.notification_preferences = NotificationPreferences(
        urgent_alert_enabled=False,
        channel_activity_enabled=True,
    )

    async def authorized_subset(
        *args: object, **kwargs: object
    ) -> tuple[EligibleReceiveGrant, ...]:
        del args, kwargs
        return (
            EligibleReceiveGrant(
                receive_grant_id=uuid.uuid4(),
                account_id=allowed.id,
                device_id=uuid.uuid4(),
                participant_ref="allowed-participant",
            ),
            EligibleReceiveGrant(
                receive_grant_id=uuid.uuid4(),
                account_id=opted_out.id,
                device_id=uuid.uuid4(),
                participant_ref="opted-out-participant",
            ),
        )

    payload = UrgentAlertNotificationPayload(
        message="Disabled vehicle ahead.",
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    key = "urgent-test-idempotency-key"

    try:
        async with factory() as db:
            db.add_all((sender, allowed, denied, opted_out, sender_session))
            await db.commit()

            first = await compose_authorized_notifications(
                db,
                sender_account_id=sender.id,
                sender_device_id=sender_device.id,
                payload=payload,
                idempotency_key=key,
                settings=settings,
                now=now,
                eligibility_finder=authorized_subset,
            )
            assert len(first) == 1

            allowed_rows = await db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.account_id == allowed.id)
            )
            denied_rows = await db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.account_id == denied.id)
            )
            opted_out_rows = await db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.account_id == opted_out.id)
            )
            assert allowed_rows == 1
            assert denied_rows == 0
            assert opted_out_rows == 0

            replay = await compose_authorized_notifications(
                db,
                sender_account_id=sender.id,
                sender_device_id=sender_device.id,
                payload=payload,
                idempotency_key=key,
                settings=settings,
                now=now + timedelta(seconds=1),
                eligibility_finder=authorized_subset,
            )
            assert [item.id for item in replay] == [item.id for item in first]

            changed_payload = UrgentAlertNotificationPayload(
                message="Different alert content.",
                issued_at=now,
                expires_at=now + timedelta(minutes=5),
            )
            with pytest.raises(NotificationError) as collision:
                await compose_authorized_notifications(
                    db,
                    sender_account_id=sender.id,
                    sender_device_id=sender_device.id,
                    payload=changed_payload,
                    idempotency_key=key,
                    settings=settings,
                    now=now + timedelta(seconds=2),
                    eligibility_finder=authorized_subset,
                )
            assert collision.value.code == "NOTIFICATION_IDEMPOTENCY_CONFLICT"

            await db.execute(delete(Notification).where(Notification.id == first[0].id))
            await db.commit()
            receipt = await db.get(
                NotificationDeliveryReceipt,
                (allowed.id, hashlib.sha256(key.encode()).hexdigest()),
            )
            assert receipt is not None
            assert receipt.notification_id is None

            with pytest.raises(NotificationError) as deleted_replay:
                await compose_authorized_notifications(
                    db,
                    sender_account_id=sender.id,
                    sender_device_id=sender_device.id,
                    payload=payload,
                    idempotency_key=key,
                    settings=settings,
                    now=now + timedelta(seconds=3),
                    eligibility_finder=authorized_subset,
                )
            assert deleted_replay.value.code == "NOTIFICATION_REPLAY_NOT_AVAILABLE"

            stale_payload = UrgentAlertNotificationPayload(
                message="Expired alert.",
                issued_at=now - timedelta(minutes=6),
                expires_at=now - timedelta(minutes=1),
            )
            with pytest.raises(NotificationError) as stale:
                await compose_authorized_notifications(
                    db,
                    sender_account_id=sender.id,
                    sender_device_id=sender_device.id,
                    payload=stale_payload,
                    idempotency_key="urgent-stale-idempotency-key",
                    settings=settings,
                    now=now,
                    eligibility_finder=authorized_subset,
                )
            assert stale.value.code == "NOTIFICATION_NOT_CURRENT"

            sender_session.revoked_at = session_now
            sender_session.revoke_reason = "test_revoked"
            await db.commit()
            revoked = await compose_authorized_notifications(
                db,
                sender_account_id=sender.id,
                sender_device_id=sender_device.id,
                payload=UrgentAlertNotificationPayload(
                    message="Should not deliver.",
                    issued_at=now,
                    expires_at=now + timedelta(minutes=4),
                ),
                idempotency_key="urgent-revoked-idempotency-key",
                settings=settings,
                now=now,
                eligibility_finder=authorized_subset,
            )
            assert revoked == ()

            await db.execute(delete(Account).where(Account.id == allowed.id))
            await db.commit()
            remaining_receipts = await db.scalar(
                select(func.count())
                .select_from(NotificationDeliveryReceipt)
                .where(NotificationDeliveryReceipt.account_id == allowed.id)
            )
            assert remaining_receipts == 0
    finally:
        await engine.dispose()
