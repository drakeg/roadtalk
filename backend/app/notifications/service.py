import hashlib
import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import (
    Account,
    Channel,
    ChannelSelection,
    Notification,
    NotificationPreferences,
    Session,
)
from app.notifications.contracts import (
    ACCOUNT_MAX_TTL,
    URGENT_ALERT_DELIVERY_NOT_GUARANTEED,
    URGENT_ALERT_EMERGENCY_SERVICES_GUIDANCE,
    URGENT_ALERT_NOT_EMERGENCY_SERVICE,
    URGENT_ALERT_UNVERIFIED,
    ChannelActivityNotificationPayload,
    NotificationPayload,
    UrgentAlertNotificationPayload,
)
from app.notifications.models import NotificationDeliveryReceipt
from app.ptt.proximity import (
    EligibleReceiveGrant,
    ProximityEligibilityError,
    ProximityPolicy,
    find_eligible_receive_grants,
    proximity_policy_from_settings,
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


EligibilityFinder = Callable[..., Awaitable[tuple[EligibleReceiveGrant, ...]]]


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


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload_fingerprint(payload: NotificationPayload) -> str:
    serialized = json.dumps(
        payload.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return _digest(serialized)


def _require_current_payload(payload: NotificationPayload, *, now: datetime) -> None:
    if payload.issued_at > now or payload.expires_at <= now:
        raise NotificationError(
            "NOTIFICATION_NOT_CURRENT",
            "The notification event is not current.",
        )


def _validate_idempotency_key(idempotency_key: str) -> None:
    if not 16 <= len(idempotency_key) <= 128:
        raise NotificationError(
            "INVALID_NOTIFICATION_IDEMPOTENCY_KEY",
            "Notification idempotency key is invalid.",
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


async def store_notification_idempotent(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    payload: NotificationPayload,
    idempotency_key: str,
    now: datetime | None = None,
) -> NotificationReceipt:
    """Store one current notification while retaining only a bounded replay tombstone."""
    resolved_now = now or datetime.now(UTC)
    _require_current_payload(payload, now=resolved_now)
    _validate_idempotency_key(idempotency_key)
    await _require_active_account(db, account_id=account_id)

    key_hash = _digest(idempotency_key)
    fingerprint = _payload_fingerprint(payload)
    await db.execute(
        delete(NotificationDeliveryReceipt).where(
            NotificationDeliveryReceipt.account_id == account_id,
            NotificationDeliveryReceipt.guard_expires_at <= resolved_now,
        )
    )
    prior = await db.scalar(
        select(NotificationDeliveryReceipt)
        .where(
            NotificationDeliveryReceipt.account_id == account_id,
            NotificationDeliveryReceipt.idempotency_key_hash == key_hash,
        )
        .with_for_update()
    )
    if prior is not None:
        if prior.request_fingerprint != fingerprint:
            await db.rollback()
            raise NotificationError(
                "NOTIFICATION_IDEMPOTENCY_CONFLICT",
                "The idempotency key was already used for a different notification.",
            )
        if prior.notification_id is None:
            await db.rollback()
            raise NotificationError(
                "NOTIFICATION_REPLAY_NOT_AVAILABLE",
                "The original notification is no longer available.",
            )
        existing = await db.scalar(
            select(Notification).where(
                Notification.id == prior.notification_id,
                Notification.account_id == account_id,
                Notification.expires_at > resolved_now,
            )
        )
        if existing is None:
            await db.rollback()
            raise NotificationError(
                "NOTIFICATION_REPLAY_NOT_AVAILABLE",
                "The original notification is no longer available.",
            )
        await db.commit()
        return _notification_receipt(existing)

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
    await db.flush()
    db.add(
        NotificationDeliveryReceipt(
            account_id=account_id,
            idempotency_key_hash=key_hash,
            request_fingerprint=fingerprint,
            notification_id=notification.id,
            guard_expires_at=payload.issued_at + ACCOUNT_MAX_TTL,
        )
    )
    await db.commit()
    await db.refresh(notification)
    return _notification_receipt(notification)


async def _current_notification_policy(
    db: AsyncSession,
    *,
    sender_account_id: uuid.UUID,
    sender_device_id: uuid.UUID,
    settings: Settings,
    now: datetime,
) -> tuple[ProximityPolicy, str] | None:
    sender_active = await db.scalar(
        select(Session.id)
        .join(Account, Account.id == Session.account_id)
        .where(
            Session.account_id == sender_account_id,
            Session.device_id == sender_device_id,
            Session.revoked_at.is_(None),
            Session.expires_at > now,
            Account.status == "active",
            Account.account_type == "registered",
        )
    )
    if sender_active is None:
        return None

    row = await db.execute(
        select(ChannelSelection.channel_id, Channel.provider_room_ref, Channel.display_label)
        .join(Channel, Channel.id == ChannelSelection.channel_id)
        .where(
            ChannelSelection.account_id == sender_account_id,
            Channel.enabled.is_(True),
            Channel.closed_at.is_(None),
        )
    )
    selected = row.one_or_none()
    if selected is None:
        return None
    channel_id, room_ref, display_label = selected
    return (
        proximity_policy_from_settings(
            settings,
            channel_id=channel_id,
            room_ref=room_ref,
        ),
        display_label,
    )


async def _notification_enabled_accounts(
    db: AsyncSession,
    *,
    candidate_account_ids: set[uuid.UUID],
    notification_class: Literal["channel_activity", "urgent_alert"],
) -> tuple[uuid.UUID, ...]:
    if not candidate_account_ids:
        return ()
    rows = await db.execute(
        select(
            Account.id,
            NotificationPreferences.channel_activity_enabled,
            NotificationPreferences.urgent_alert_enabled,
        )
        .outerjoin(NotificationPreferences, NotificationPreferences.account_id == Account.id)
        .where(
            Account.id.in_(candidate_account_ids),
            Account.status == "active",
            Account.account_type == "registered",
        )
        .order_by(Account.id)
    )
    enabled: list[uuid.UUID] = []
    for account_id, channel_enabled, urgent_enabled in rows.all():
        allowed = (
            channel_enabled is not False
            if notification_class == "channel_activity"
            else urgent_enabled is not False
        )
        if allowed:
            enabled.append(account_id)
    return tuple(enabled)


async def compose_authorized_notifications(
    db: AsyncSession,
    *,
    sender_account_id: uuid.UUID,
    sender_device_id: uuid.UUID,
    payload: ChannelActivityNotificationPayload | UrgentAlertNotificationPayload,
    idempotency_key: str,
    settings: Settings,
    now: datetime | None = None,
    eligibility_finder: EligibilityFinder = find_eligible_receive_grants,
) -> tuple[NotificationReceipt, ...]:
    """Create notifications only for an already-authorized current audience."""
    resolved_now = now or datetime.now(UTC)
    _require_current_payload(payload, now=resolved_now)
    _validate_idempotency_key(idempotency_key)

    policy_context = await _current_notification_policy(
        db,
        sender_account_id=sender_account_id,
        sender_device_id=sender_device_id,
        settings=settings,
        now=resolved_now,
    )
    if policy_context is None:
        return ()
    policy, channel_label = policy_context
    if (
        isinstance(payload, ChannelActivityNotificationPayload)
        and payload.channel_label != channel_label
    ):
        raise NotificationError(
            "NOTIFICATION_CHANNEL_MISMATCH",
            "Notification channel context does not match the current authorized channel.",
        )

    try:
        eligible = await eligibility_finder(
            db,
            sender_account_id=sender_account_id,
            sender_device_id=sender_device_id,
            policy=policy,
            now=resolved_now,
        )
    except ProximityEligibilityError:
        return ()

    candidate_account_ids = {item.account_id for item in eligible}
    recipient_account_ids = await _notification_enabled_accounts(
        db,
        candidate_account_ids=candidate_account_ids,
        notification_class=payload.notification_class,
    )

    receipts: list[NotificationReceipt] = []
    for account_id in recipient_account_ids:
        receipts.append(
            await store_notification_idempotent(
                db,
                account_id=account_id,
                payload=payload,
                idempotency_key=idempotency_key,
                now=resolved_now,
            )
        )
    return tuple(receipts)


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
    await db.execute(
        delete(NotificationDeliveryReceipt).where(
            NotificationDeliveryReceipt.account_id == account_id,
            NotificationDeliveryReceipt.guard_expires_at <= resolved_now,
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
