import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.notifications.provider import (
    DisabledNotificationProvider,
    FakeNotificationProvider,
    NotificationDeliveryBoundary,
    NotificationDeliveryRequest,
    NotificationDeliveryResult,
    NotificationDeliveryStatus,
    NotificationProviderUnavailable,
    build_notification_provider,
)


def request(now: datetime | None = None) -> NotificationDeliveryRequest:
    issued_at = now or datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
    return NotificationDeliveryRequest(
        notification_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        notification_class="urgent_alert",
        priority="urgent",
        issued_at=issued_at,
        expires_at=issued_at + timedelta(minutes=5),
    )


def test_fake_provider_is_deterministic_and_bounded() -> None:
    now = datetime(2026, 9, 2, 12, 1, tzinfo=UTC)
    value = request(now - timedelta(minutes=1))
    provider = FakeNotificationProvider(clock=lambda: now)
    result = asyncio.run(provider.deliver(value))

    assert result.notification_id == value.notification_id
    assert result.status == NotificationDeliveryStatus.ACCEPTED
    assert result.provider_version == "fake-v1"
    assert result.attempted_at == now
    assert result.expires_at == value.expires_at
    dumped = result.model_dump()
    assert "read" not in dumped
    assert "respond" not in dumped
    assert "push_token" not in dumped


def test_disabled_provider_fails_closed() -> None:
    with pytest.raises(NotificationProviderUnavailable, match="notification delivery unavailable"):
        asyncio.run(DisabledNotificationProvider().deliver(request()))


def test_boundary_rejects_expired_and_mismatched_results() -> None:
    now = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
    expired = request(now - timedelta(minutes=10))
    boundary = NotificationDeliveryBoundary(
        FakeNotificationProvider(clock=lambda: now),
        clock=lambda: now,
    )
    with pytest.raises(NotificationProviderUnavailable, match="notification delivery unavailable"):
        asyncio.run(boundary.deliver(expired))

    current = request(now)

    class MismatchedProvider:
        async def deliver(self, value: NotificationDeliveryRequest) -> NotificationDeliveryResult:
            return NotificationDeliveryResult(
                notification_id=uuid.uuid4(),
                status=NotificationDeliveryStatus.ACCEPTED,
                provider_version="fake-v1",
                attempted_at=now + timedelta(seconds=1),
                expires_at=value.expires_at,
            )

    mismatched = NotificationDeliveryBoundary(MismatchedProvider(), clock=lambda: now)
    with pytest.raises(NotificationProviderUnavailable, match="notification delivery unavailable"):
        asyncio.run(mismatched.deliver(current))


def test_builder_allows_only_disabled_or_local_test_fake() -> None:
    assert isinstance(build_notification_provider(), DisabledNotificationProvider)
    assert isinstance(
        build_notification_provider("fake", environment="test"), FakeNotificationProvider
    )
    with pytest.raises(NotificationProviderUnavailable, match="notification delivery unavailable"):
        build_notification_provider("fake", environment="production")


def test_contract_forbids_external_delivery_material() -> None:
    fields = set(NotificationDeliveryRequest.model_fields)
    assert fields == {
        "notification_id",
        "account_id",
        "notification_class",
        "priority",
        "issued_at",
        "expires_at",
    }
    forbidden = {
        "device_id",
        "push_token",
        "url",
        "api_key",
        "credential",
        "latitude",
        "longitude",
        "route",
        "corridor",
        "message",
    }
    assert fields.isdisjoint(forbidden)
