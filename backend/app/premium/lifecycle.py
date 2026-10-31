from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.premium.contracts import EntitlementState, SubscriptionState

LifecycleAction = Literal["activate", "renew", "cancel", "expire", "revoke"]


class PremiumLifecycleError(RuntimeError):
    """Stable non-disclosing Premium lifecycle failure."""


class PremiumLifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: uuid.UUID
    subscription_id: uuid.UUID
    account_id: uuid.UUID
    action: LifecycleAction
    effective_at: datetime
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_expiry(self) -> PremiumLifecycleEvent:
        if self.action in {"activate", "renew"}:
            if self.expires_at is None or self.expires_at <= self.effective_at:
                raise ValueError("activation and renewal require a future expiry")
        elif self.expires_at is not None and self.expires_at < self.effective_at:
            raise ValueError("expiry cannot precede the lifecycle event")
        return self


class PremiumLifecycleReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: uuid.UUID
    subscription_id: uuid.UUID
    account_id: uuid.UUID
    subscription_state: SubscriptionState
    entitlement_state: EntitlementState
    effective_at: datetime
    expires_at: datetime | None = None
    replayed: bool = False
    server_authoritative: Literal[True] = True
    communication_authorization_unchanged: Literal[True] = True


@dataclass(frozen=True, slots=True)
class _LifecycleRecord:
    subscription_id: uuid.UUID
    account_id: uuid.UUID
    subscription_state: SubscriptionState
    entitlement_state: EntitlementState
    effective_at: datetime
    expires_at: datetime | None


class PremiumLifecycle:
    """Deterministic in-memory lifecycle used by local code and CI."""

    def __init__(self) -> None:
        self._records: dict[uuid.UUID, _LifecycleRecord] = {}
        self._events: dict[uuid.UUID, PremiumLifecycleEvent] = {}
        self._receipts: dict[uuid.UUID, PremiumLifecycleReceipt] = {}
        self._lock = RLock()

    def apply(self, event: PremiumLifecycleEvent) -> PremiumLifecycleReceipt:
        normalized = self._normalized_event(event)
        with self._lock:
            replay = self._receipts.get(normalized.event_id)
            if replay is not None:
                prior_event = self._events[normalized.event_id]
                if prior_event != normalized:
                    raise PremiumLifecycleError("Premium lifecycle unavailable")
                return replay.model_copy(update={"replayed": True})

            current = self._records.get(normalized.subscription_id)
            if current is not None:
                self._validate_identity(current, normalized)
                if normalized.effective_at < current.effective_at:
                    raise PremiumLifecycleError("Premium lifecycle unavailable")

            record = self._transition(current, normalized)
            receipt = PremiumLifecycleReceipt(
                event_id=normalized.event_id,
                subscription_id=record.subscription_id,
                account_id=record.account_id,
                subscription_state=record.subscription_state,
                entitlement_state=record.entitlement_state,
                effective_at=record.effective_at,
                expires_at=record.expires_at,
            )
            self._records[record.subscription_id] = record
            self._events[normalized.event_id] = normalized
            self._receipts[normalized.event_id] = receipt
            return receipt

    def current(
        self,
        subscription_id: uuid.UUID,
        *,
        observed_at: datetime,
    ) -> PremiumLifecycleReceipt | None:
        observed = self._as_utc(observed_at)
        with self._lock:
            record = self._records.get(subscription_id)
            if record is None:
                return None

            subscription_state = record.subscription_state
            entitlement_state = record.entitlement_state

            if (
                record.expires_at is not None
                and observed >= record.expires_at
                and record.subscription_state in {"active", "grace", "canceled"}
            ):
                subscription_state = "expired"
                entitlement_state = "expired"

            return PremiumLifecycleReceipt(
                event_id=uuid.UUID(int=0),
                subscription_id=record.subscription_id,
                account_id=record.account_id,
                subscription_state=subscription_state,
                entitlement_state=entitlement_state,
                effective_at=observed,
                expires_at=record.expires_at,
            )

    def _transition(
        self,
        current: _LifecycleRecord | None,
        event: PremiumLifecycleEvent,
    ) -> _LifecycleRecord:
        if event.action == "activate":
            if current is not None and current.subscription_state not in {
                "inactive",
                "expired",
                "revoked",
            }:
                raise PremiumLifecycleError("Premium lifecycle unavailable")
            return self._record(event, "active", "active")

        if current is None:
            raise PremiumLifecycleError("Premium lifecycle unavailable")

        if event.action == "renew":
            if current.subscription_state not in {"active", "grace", "canceled"}:
                raise PremiumLifecycleError("Premium lifecycle unavailable")
            return self._record(event, "active", "active")

        if event.action == "cancel":
            if current.subscription_state not in {"active", "grace"}:
                raise PremiumLifecycleError("Premium lifecycle unavailable")
            expiry = current.expires_at
            if expiry is None or event.effective_at >= expiry:
                return self._record(event, "expired", "expired", expires_at=expiry)
            return self._record(event, "canceled", "active", expires_at=expiry)

        if event.action == "expire":
            if current.subscription_state not in {"active", "grace", "canceled"}:
                raise PremiumLifecycleError("Premium lifecycle unavailable")
            expiry = current.expires_at
            if expiry is not None and event.effective_at < expiry:
                raise PremiumLifecycleError("Premium lifecycle unavailable")
            return self._record(event, "expired", "expired", expires_at=expiry)

        if event.action == "revoke":
            if current.subscription_state == "revoked":
                raise PremiumLifecycleError("Premium lifecycle unavailable")
            return self._record(event, "revoked", "revoked", expires_at=current.expires_at)

        raise PremiumLifecycleError("Premium lifecycle unavailable")

    def _record(
        self,
        event: PremiumLifecycleEvent,
        subscription_state: SubscriptionState,
        entitlement_state: EntitlementState,
        *,
        expires_at: datetime | None = None,
    ) -> _LifecycleRecord:
        return _LifecycleRecord(
            subscription_id=event.subscription_id,
            account_id=event.account_id,
            subscription_state=subscription_state,
            entitlement_state=entitlement_state,
            effective_at=event.effective_at,
            expires_at=event.expires_at if expires_at is None else expires_at,
        )

    @staticmethod
    def _validate_identity(
        current: _LifecycleRecord,
        event: PremiumLifecycleEvent,
    ) -> None:
        if current.account_id != event.account_id:
            raise PremiumLifecycleError("Premium lifecycle unavailable")

    @staticmethod
    def _normalized_event(event: PremiumLifecycleEvent) -> PremiumLifecycleEvent:
        return event.model_copy(
            update={
                "effective_at": PremiumLifecycle._as_utc(event.effective_at),
                "expires_at": (
                    PremiumLifecycle._as_utc(event.expires_at)
                    if event.expires_at is not None
                    else None
                ),
            }
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            raise PremiumLifecycleError("Premium lifecycle unavailable")
        return value.astimezone(UTC)
