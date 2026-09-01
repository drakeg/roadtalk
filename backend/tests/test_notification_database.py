import asyncio
import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, Notification
from app.notifications.contracts import (
    ChannelActivityNotificationPayload,
    UrgentAlertNotificationPayload,
)
from app.notifications.service import (
    NotificationError,
    get_preferences,
    list_notifications,
    store_notification,
    update_notification_state,
    update_preferences,
)


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_notification_account_lifecycle() -> None:
    asyncio.run(_notification_lifecycle())


async def _notification_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    account = Account()
    now = datetime.now(UTC)

    try:
        async with factory() as db:
            db.add(account)
            await db.commit()
            account_id = account.id

            defaults = await get_preferences(db, account_id=account_id)
            assert defaults.channel_activity_enabled is True
            assert defaults.urgent_alert_enabled is True
            assert defaults.version == 1

            changed = await update_preferences(
                db,
                account_id=account_id,
                channel_activity_enabled=False,
                urgent_alert_enabled=True,
                expected_version=1,
            )
            assert changed.version == 2

            replay = await update_preferences(
                db,
                account_id=account_id,
                channel_activity_enabled=False,
                urgent_alert_enabled=True,
                expected_version=1,
            )
            assert replay.version == 2

            with pytest.raises(NotificationError) as conflict:
                await update_preferences(
                    db,
                    account_id=account_id,
                    channel_activity_enabled=True,
                    urgent_alert_enabled=True,
                    expected_version=1,
                )
            assert conflict.value.code == "NOTIFICATION_PREFERENCES_VERSION_CONFLICT"

            stored = await store_notification(
                db,
                account_id=account_id,
                payload=ChannelActivityNotificationPayload(
                    priority="normal",
                    title="Channel activity",
                    message="There is current activity on your selected channel.",
                    channel_label="General",
                    issued_at=now,
                    expires_at=now + timedelta(hours=1),
                ),
            )
            assert stored.version == 1

            urgent = await store_notification(
                db,
                account_id=account_id,
                payload=UrgentAlertNotificationPayload(
                    message="Disabled vehicle ahead.",
                    issued_at=now,
                    expires_at=now + timedelta(minutes=5),
                ),
            )
            assert urgent.verified is False
            assert urgent.emergency_service is False
            assert urgent.delivery_guaranteed is False
            assert urgent.safety_not_emergency_service == ("RoadTalk is not an emergency service.")

            listed = await list_notifications(db, account_id=account_id, now=now)
            assert {item.id for item in listed} == {stored.id, urgent.id}

            read = await update_notification_state(
                db,
                account_id=account_id,
                notification_id=stored.id,
                state="read",
                expected_version=1,
                now=now + timedelta(minutes=1),
            )
            assert read.read_at is not None
            assert read.version == 2

            dismissed = await update_notification_state(
                db,
                account_id=account_id,
                notification_id=stored.id,
                state="dismissed",
                expected_version=2,
                now=now + timedelta(minutes=2),
            )
            assert dismissed.dismissed_at is not None
            assert dismissed.version == 3
            remaining_inbox = await list_notifications(db, account_id=account_id, now=now)
            assert [item.id for item in remaining_inbox] == [urgent.id]

            other_account = Account()
            db.add(other_account)
            await db.commit()
            with pytest.raises(NotificationError) as unavailable:
                await update_notification_state(
                    db,
                    account_id=other_account.id,
                    notification_id=urgent.id,
                    state="read",
                    expected_version=1,
                    now=now + timedelta(minutes=1),
                )
            assert unavailable.value.code == "NOTIFICATION_NOT_AVAILABLE"
            await db.rollback()

            assert (
                await list_notifications(db, account_id=account_id, now=now + timedelta(minutes=6))
                == ()
            )
            assert await db.get(Notification, urgent.id) is None

            await db.execute(delete(Account).where(Account.id == account_id))
            await db.commit()
            remaining = await db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.account_id == account_id)
            )
            assert remaining == 0
    finally:
        await engine.dispose()
