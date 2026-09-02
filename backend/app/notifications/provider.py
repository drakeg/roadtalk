from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NotificationDeliveryStatus(StrEnum):
    ACCEPTED = "accepted"
    DISABLED = "disabled"


class NotificationDeliveryRequest(BaseModel):
    """Minimal server-internal request after authorization and inbox persistence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    notification_id: uuid.UUID
    account_id: uuid.UUID
    notification_class: Literal["account", "channel_activity", "urgent_alert"]
    priority: Literal["normal", "high", "urgent"]
    issued_at: datetime
    expires_at: datetime

    @field_validator("issued_at", "expires_at")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("notification delivery timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def expiry_must_follow_issue(self) -> NotificationDeliveryRequest:
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        return self


class NotificationDeliveryResult(BaseModel):
    """Bounded provider result; never represents human read or response state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    notification_id: uuid.UUID
    status: NotificationDeliveryStatus
    provider_version: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$")
    attempted_at: datetime
    expires_at: datetime

    @field_validator("attempted_at", "expires_at")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("notification delivery timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def expiry_must_follow_attempt(self) -> NotificationDeliveryResult:
        if self.expires_at <= self.attempted_at:
            raise ValueError("expires_at must be after attempted_at")
        return self


class NotificationProviderError(RuntimeError):
    """Stable non-disclosing notification provider failure."""


class NotificationProviderUnavailable(NotificationProviderError):
    """Provider could not produce a usable delivery result."""


class NotificationProvider(Protocol):
    async def deliver(self, request: NotificationDeliveryRequest) -> NotificationDeliveryResult: ...


class DisabledNotificationProvider:
    async def deliver(self, request: NotificationDeliveryRequest) -> NotificationDeliveryResult:
        del request
        raise NotificationProviderUnavailable("notification delivery unavailable")


class FakeNotificationProvider:
    """Deterministic local/CI provider with no network or account dependency."""

    def __init__(
        self,
        outcomes: Mapping[uuid.UUID, NotificationDeliveryStatus] | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._outcomes = dict(outcomes or {})
        self._clock = clock or (lambda: datetime.now(UTC))

    async def deliver(self, request: NotificationDeliveryRequest) -> NotificationDeliveryResult:
        attempted_at = self._clock().astimezone(UTC)
        if request.expires_at <= attempted_at:
            raise NotificationProviderUnavailable("notification delivery unavailable")
        status = self._outcomes.get(request.notification_id, NotificationDeliveryStatus.ACCEPTED)
        return NotificationDeliveryResult(
            notification_id=request.notification_id,
            status=status,
            provider_version="fake-v1",
            attempted_at=attempted_at,
            expires_at=request.expires_at,
        )


class NotificationDeliveryBoundary:
    """Timeout and integrity boundary around the configured delivery provider."""

    def __init__(
        self,
        provider: NotificationProvider,
        *,
        timeout_ms: int = 250,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not 10 <= timeout_ms <= 2_000:
            raise ValueError("notification provider timeout is out of bounds")
        self._provider = provider
        self._timeout_seconds = timeout_ms / 1_000
        self._clock = clock or (lambda: datetime.now(UTC))

    async def deliver(self, request: NotificationDeliveryRequest) -> NotificationDeliveryResult:
        now = self._clock().astimezone(UTC)
        if request.expires_at <= now:
            raise NotificationProviderUnavailable("notification delivery unavailable")
        try:
            result = await asyncio.wait_for(
                self._provider.deliver(request),
                timeout=self._timeout_seconds,
            )
        except Exception:
            raise NotificationProviderUnavailable("notification delivery unavailable") from None
        if result.notification_id != request.notification_id:
            raise NotificationProviderUnavailable("notification delivery unavailable")
        if result.expires_at != request.expires_at:
            raise NotificationProviderUnavailable("notification delivery unavailable")
        if result.attempted_at < request.issued_at or result.expires_at <= now:
            raise NotificationProviderUnavailable("notification delivery unavailable")
        return result


def build_notification_provider(
    provider: Literal["disabled", "fake"] = "disabled",
    *,
    environment: Literal["local", "test", "field-test", "production"] = "local",
    outcomes: Mapping[uuid.UUID, NotificationDeliveryStatus] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> NotificationProvider:
    if environment not in {"local", "test"} and provider != "disabled":
        raise NotificationProviderUnavailable("notification delivery unavailable")
    if provider == "disabled":
        return DisabledNotificationProvider()
    if provider == "fake":
        return FakeNotificationProvider(outcomes, clock=clock)
    raise NotificationProviderUnavailable("notification delivery unavailable")
