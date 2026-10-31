from __future__ import annotations

import hashlib
import hmac
import uuid
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Final

from pydantic import BaseModel, ConfigDict

MAX_PREMIUM_WEBHOOK_BYTES: Final = 64 * 1024
MAX_PREMIUM_WEBHOOK_AGE: Final = timedelta(minutes=5)
MAX_PREMIUM_WEBHOOK_FUTURE_SKEW: Final = timedelta(seconds=30)


class PremiumWebhookError(RuntimeError):
    """Stable non-disclosing webhook-boundary failure."""


class PremiumWebhookReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: uuid.UUID
    accepted_at: datetime
    replayed: bool = False


class PremiumWebhookBoundary:
    """Deterministic authenticity/replay boundary for a future provider webhook.

    D08 does not expose an HTTP route and does not activate a provider. The
    boundary is exercised only with local/test secrets and payloads.
    """

    def __init__(
        self,
        *,
        secret: bytes,
        max_events: int = 10_000,
    ) -> None:
        if len(secret) < 32:
            raise ValueError("Premium webhook secret is too short")
        if max_events < 1:
            raise ValueError("Premium webhook replay bound is invalid")
        self._secret = secret
        self._max_events = max_events
        self._seen: dict[uuid.UUID, bytes] = {}
        self._order: deque[uuid.UUID] = deque()

    def verify(
        self,
        *,
        event_id: uuid.UUID,
        timestamp: datetime,
        body: bytes,
        signature: str,
        now: datetime,
    ) -> PremiumWebhookReceipt:
        observed = self._as_utc(now)
        event_time = self._as_utc(timestamp)
        if len(body) > MAX_PREMIUM_WEBHOOK_BYTES:
            raise PremiumWebhookError("Premium webhook unavailable")
        if (
            event_time < observed - MAX_PREMIUM_WEBHOOK_AGE
            or event_time > observed + MAX_PREMIUM_WEBHOOK_FUTURE_SKEW
        ):
            raise PremiumWebhookError("Premium webhook unavailable")

        expected = hmac.new(
            self._secret,
            self._signed_bytes(event_id=event_id, timestamp=event_time, body=body),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise PremiumWebhookError("Premium webhook unavailable")

        digest = hashlib.sha256(body).digest()
        prior = self._seen.get(event_id)
        if prior is not None:
            if prior != digest:
                raise PremiumWebhookError("Premium webhook unavailable")
            return PremiumWebhookReceipt(
                event_id=event_id,
                accepted_at=observed,
                replayed=True,
            )

        if len(self._seen) >= self._max_events:
            evicted = self._order.popleft()
            self._seen.pop(evicted, None)
        self._seen[event_id] = digest
        self._order.append(event_id)
        return PremiumWebhookReceipt(event_id=event_id, accepted_at=observed)

    def sign_for_test(
        self,
        *,
        event_id: uuid.UUID,
        timestamp: datetime,
        body: bytes,
    ) -> str:
        """Local/test helper; no provider credential is configured or persisted."""

        return hmac.new(
            self._secret,
            self._signed_bytes(
                event_id=event_id,
                timestamp=self._as_utc(timestamp),
                body=body,
            ),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _signed_bytes(*, event_id: uuid.UUID, timestamp: datetime, body: bytes) -> bytes:
        stamp = timestamp.isoformat().encode("ascii")
        return event_id.bytes + b"." + stamp + b"." + body

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            raise PremiumWebhookError("Premium webhook unavailable")
        return value.astimezone(UTC)
