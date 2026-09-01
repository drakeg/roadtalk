from datetime import UTC, datetime, timedelta

import pytest
from pydantic import TypeAdapter, ValidationError

from app.notifications.contracts import (
    ACCOUNT_MAX_TTL,
    CHANNEL_ACTIVITY_MAX_TTL,
    PROHIBITED_NOTIFICATION_FIELDS,
    URGENT_ALERT_DELIVERY_NOT_GUARANTEED,
    URGENT_ALERT_EMERGENCY_SERVICES_GUIDANCE,
    URGENT_ALERT_MAX_TTL,
    URGENT_ALERT_NOT_EMERGENCY_SERVICE,
    URGENT_ALERT_UNVERIFIED,
    AccountNotificationPayload,
    ChannelActivityNotificationPayload,
    NotificationPayload,
    UrgentAlertCommand,
    UrgentAlertNotificationPayload,
)

NOW = datetime(2026, 8, 31, 22, 0, tzinfo=UTC)


def test_notification_classes_are_closed_and_ttl_bounded() -> None:
    account = AccountNotificationPayload(
        priority="high",
        title="Session changed",
        message="Your RoadTalk session changed.",
        issued_at=NOW,
        expires_at=NOW + ACCOUNT_MAX_TTL,
    )
    channel = ChannelActivityNotificationPayload(
        priority="normal",
        title="Channel activity",
        message="There is current activity on your selected channel.",
        channel_label="General",
        issued_at=NOW,
        expires_at=NOW + CHANNEL_ACTIVITY_MAX_TTL,
    )
    urgent = UrgentAlertNotificationPayload(
        message="Disabled vehicle ahead. Use caution.",
        issued_at=NOW,
        expires_at=NOW + URGENT_ALERT_MAX_TTL,
    )

    adapter: TypeAdapter[NotificationPayload] = TypeAdapter(NotificationPayload)
    assert adapter.validate_python(account.model_dump()).notification_class == "account"
    assert adapter.validate_python(channel.model_dump()).notification_class == "channel_activity"
    assert adapter.validate_python(urgent.model_dump()).notification_class == "urgent_alert"

    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "notification_class": "marketing",
                "priority": "normal",
                "source": "roadtalk_account",
                "title": "Nope",
                "message": "Not an approved class.",
                "issued_at": NOW,
                "expires_at": NOW + timedelta(minutes=1),
            }
        )


def test_urgent_alert_contract_is_unverified_non_dispatch_and_non_guaranteed() -> None:
    payload = UrgentAlertNotificationPayload(
        message="Road obstruction ahead.",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )

    assert payload.priority == "urgent"
    assert payload.verified is False
    assert payload.emergency_service is False
    assert payload.delivery_guaranteed is False
    assert payload.safety_not_emergency_service == URGENT_ALERT_NOT_EMERGENCY_SERVICE
    assert payload.safety_delivery_not_guaranteed == URGENT_ALERT_DELIVERY_NOT_GUARANTEED
    assert payload.safety_emergency_services_guidance == URGENT_ALERT_EMERGENCY_SERVICES_GUIDANCE
    assert payload.safety_unverified == URGENT_ALERT_UNVERIFIED


def test_urgent_alert_lifetime_is_short_and_cannot_silently_extend() -> None:
    with pytest.raises(ValidationError, match="allowed lifetime"):
        UrgentAlertNotificationPayload(
            message="Help requested.",
            issued_at=NOW,
            expires_at=NOW + URGENT_ALERT_MAX_TTL + timedelta(seconds=1),
        )

    with pytest.raises(ValidationError, match="after issued_at"):
        UrgentAlertNotificationPayload(
            message="Help requested.",
            issued_at=NOW,
            expires_at=NOW,
        )


def test_urgent_alert_command_has_no_targeting_or_provider_controls() -> None:
    command = UrgentAlertCommand(
        message="Vehicle stopped in travel lane.",
        idempotency_key="urgent-command-0001",
    )
    assert set(command.model_dump()) == {"message", "idempotency_key"}

    for forbidden in sorted(PROHIBITED_NOTIFICATION_FIELDS):
        with pytest.raises(ValidationError):
            UrgentAlertCommand.model_validate(
                {
                    "message": "Vehicle stopped in travel lane.",
                    "idempotency_key": "urgent-command-0001",
                    forbidden: "attacker-controlled",
                }
            )


def test_public_notification_payloads_reject_sensitive_or_targeting_fields() -> None:
    base = {
        "notification_class": "urgent_alert",
        "message": "Use caution ahead.",
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
    }
    adapter: TypeAdapter[NotificationPayload] = TypeAdapter(NotificationPayload)

    for forbidden in sorted(PROHIBITED_NOTIFICATION_FIELDS):
        with pytest.raises(ValidationError):
            adapter.validate_python({**base, forbidden: "forbidden"})


def test_urgent_alert_safety_fields_cannot_be_overridden() -> None:
    overrides = {
        "verified": True,
        "emergency_service": True,
        "delivery_guaranteed": True,
        "safety_not_emergency_service": "911 dispatched",
        "safety_delivery_not_guaranteed": "Guaranteed",
        "safety_emergency_services_guidance": "Wait for RoadTalk",
        "safety_unverified": "Verified bulletin",
    }
    for field, value in overrides.items():
        with pytest.raises(ValidationError):
            UrgentAlertNotificationPayload.model_validate(
                {
                    "message": "Use caution ahead.",
                    "issued_at": NOW,
                    "expires_at": NOW + timedelta(minutes=5),
                    field: value,
                }
            )


def test_notification_timestamps_require_explicit_timezone() -> None:
    with pytest.raises(ValidationError):
        AccountNotificationPayload(
            priority="normal",
            title="Session notice",
            message="Your RoadTalk session changed.",
            issued_at=NOW.replace(tzinfo=None),
            expires_at=(NOW + timedelta(minutes=5)).replace(tzinfo=None),
        )


def test_urgent_alert_idempotency_key_is_transport_safe() -> None:
    for invalid in ("contains spaces 0001", "contains/slash/0001", "contains\\nnewline0001"):
        with pytest.raises(ValidationError):
            UrgentAlertCommand(message="Use caution ahead.", idempotency_key=invalid)

    accepted = UrgentAlertCommand(
        message="Use caution ahead.", idempotency_key="urgent.alert_0001~retry"
    )
    assert accepted.idempotency_key == "urgent.alert_0001~retry"
