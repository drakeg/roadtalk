import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Account, Notification, NotificationPreferences
from app.notifications.contracts import (
    URGENT_ALERT_DELIVERY_NOT_GUARANTEED,
    URGENT_ALERT_EMERGENCY_SERVICES_GUIDANCE,
    URGENT_ALERT_NOT_EMERGENCY_SERVICE,
    URGENT_ALERT_UNVERIFIED,
    NotificationPayload,
)

INBOX_LIMIT = 50


class NotificationError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class PreferencesReceipt:
    channel_activity_enabled: bool
    urgent_alert_enabled: bool
    version: int


@dataclass(frozen=True)
class NotificationReceipt:
    id: uuid.UUID
    notification_class: str
    priority: str
    source: str
    title: str | None
    message: str
    channel_label: str | None
    issued_at: datetime
    expires_at: datetime
    read_at: datetime | None
    dismissed_at: datetime | None
    version: int
    verified: bool | None
    emergency_service: bool | None
    delivery_guaranteed: bool | None
    safety_not_emergency_service: str | None
    safety_delivery_not_guaranteed: str | None
    safety_emergency_services_guidance: str | None
    safety_unverified: str | None


def _preference_receipt(value: NotificationPreferences) -> PreferencesReceipt:
    return PreferencesReceipt(
        channel_activity_enabled=value.channel_activity_enabled,
        urgent_alert_enabled=value.urgent_alert_enabled,
        version=value.version,
    )


def _notification_receipt(value: Notification) -> NotificationReceipt:
    urgent = value.notification_class == "urgent_alert"
    return NotificationReceipt(
        id=value.id,
        notification_class=value.notification_class,
        priority=value.priority,
        source=value.source,
        title=value.title,
        message=value.message,
        channel_label=value.channel_label,
        issued_at=value.issued_at,
        expires_at=value.expires_at,
        read_at=value.read_at,
        dismissed_at=value.dismissed_at,
        version=value.version,
        verified=False if urgent else None,
        emergency_service=False if urgent else None,
        delivery_guaranteed=False if urgent else None,
        safety_not_emergency_service=(URGENT_ALERT_NOT_EMERGENCY_SERVICE if urgent else None),
        safety_delivery_not_guaranteed=(URGENT_ALERT_DELIVERY_NOT_GUARANTEED if urgent else None),
        safety_emergency_services_guidance=(
            URGENT_ALERT_EMERGENCY_SERVICES_GUIDANCE if urgent else None
        ),
        safety_unverified=URGENT_ALERT_UNVERIFIED if urgent else None,
    )


async def _require_active_account(db: AsyncSession, *, account_id: uuid.UUID) -> None:
    account = await db.scalar(select(Account).where(Account.id == account_id))
    if account is None or account.status != "active":
        raise NotificationError("NOTIFICATIONS_UNAVAILABLE", "Notifications are unavailable.")


async def _locked_preferences(
    db: AsyncSession, *, account_id: uuid.UUID
) -> NotificationPreferences:
    account = await db.scalar(select(Account).where(Account.id == account_id).with_for_update())
    if account is None or account.status != "active":
        raise NotificationError("NOTIFICATIONS_UNAVAILABLE", "Notifications are unavailable.")
    preferences = await db.scalar(
        select(NotificationPreferences)
        .where(NotificationPreferences.account_id == account_id)
        .with_for_update()
    )
    if preferences is None:
        preferences = NotificationPreferences(account_id=account_id)
        db.add(preferences)
        await db.flush()
    return preferences


async def get_preferences(db: AsyncSession, *, account_id: uuid.UUID) -> PreferencesReceipt:
    preferences = await _locked_preferences(db, account_id=account_id)
    await db.commit()
    return _preference_receipt(preferences)


async def update_preferences(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    channel_activity_enabled: bool,
    urgent_alert_enabled: bool,
    expected_version: int,
) -> PreferencesReceipt:
    preferences = await _locked_preferences(db, account_id=account_id)
    requested = (channel_activity_enabled, urgent_alert_enabled)
    current = (preferences.channel_activity_enabled, preferences.urgent_alert_enabled)
    if expected_version == preferences.version:
        if requested != current:
            preferences.channel_activity_enabled = channel_activity_enabled
            preferences.urgent_alert_enabled = urgent_alert_enabled
            preferences.version += 1
        await db.commit()
        return _preference_receipt(preferences)
    if expected_version + 1 == preferences.version and requested == current:
        await db.commit()
        return _preference_receipt(preferences)
    await db.rollback()
    raise NotificationError(
        "NOTIFICATION_PREFERENCES_VERSION_CONFLICT",
        "Notification preferences changed; reload them before retrying.",
    )


async def store_notification(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    payload: NotificationPayload,
) -> NotificationReceipt:
    await _require_active_account(db, account_id=account_id)
    values = payload.model_dump()
    notification = Notification(
        account_id=account_id,
        notification_class=values["notification_class"],
        priority=values["priority"],
        source=values["source"],
        title=values.get("title"),
        message=values["message"],
        channel_label=values.get("channel_label"),
        issued_at=values["issued_at"],
        expires_at=values["expires_at"],
        version=1,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return _notification_receipt(notification)


async def list_notifications(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    now: datetime | None = None,
) -> tuple[NotificationReceipt, ...]:
    await _require_active_account(db, account_id=account_id)
    resolved_now = now or datetime.now(UTC)
    await db.execute(
        delete(Notification).where(
            Notification.account_id == account_id,
            Notification.expires_at <= resolved_now,
        )
    )
    rows = (
        await db.scalars(
            select(Notification)
            .where(
                Notification.account_id == account_id,
                Notification.expires_at > resolved_now,
                Notification.dismissed_at.is_(None),
            )
            .order_by(Notification.issued_at.desc(), Notification.id.desc())
            .limit(INBOX_LIMIT)
        )
    ).all()
    await db.commit()
    return tuple(_notification_receipt(row) for row in rows)


async def update_notification_state(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    notification_id: uuid.UUID,
    state: Literal["read", "dismissed"],
    expected_version: int,
    now: datetime | None = None,
) -> NotificationReceipt:
    await _require_active_account(db, account_id=account_id)
    resolved_now = now or datetime.now(UTC)
    notification = await db.scalar(
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.account_id == account_id,
            Notification.expires_at > resolved_now,
        )
        .with_for_update()
    )
    if notification is None:
        raise NotificationError("NOTIFICATION_NOT_AVAILABLE", "The notification is unavailable.")
    already_applied = (
        notification.dismissed_at is not None
        if state == "dismissed"
        else notification.read_at is not None
    )
    if expected_version == notification.version:
        if not already_applied:
            if state == "dismissed":
                notification.dismissed_at = resolved_now
                notification.read_at = notification.read_at or resolved_now
            else:
                notification.read_at = resolved_now
            notification.version += 1
        await db.commit()
        return _notification_receipt(notification)
    if expected_version + 1 == notification.version and already_applied:
        await db.commit()
        return _notification_receipt(notification)
    await db.rollback()
    raise NotificationError(
        "NOTIFICATION_VERSION_CONFLICT",
        "The notification changed; reload it before retrying.",
    )
