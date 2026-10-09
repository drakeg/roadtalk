from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Mapping
from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from app.premium.contracts import SubscriptionState

PREMIUM_PROVIDER_TIMEOUT_MS = 500


class PremiumProviderMode(StrEnum):
    DISABLED = "disabled"
    TEST = "test"


class PremiumProviderHealth(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: PremiumProviderMode
    available: bool


class PremiumProviderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: uuid.UUID
    account_id: uuid.UUID
    operation: Literal["subscription_status"] = "subscription_status"


class PremiumProviderResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: uuid.UUID
    account_id: uuid.UUID
    subscription_state: SubscriptionState
    provider_mode: Literal["test"] = "test"
    provider_version: Literal["test-v1"] = "test-v1"


class PremiumProviderError(RuntimeError):
    """Stable non-disclosing Premium provider failure."""


class PremiumProviderUnavailable(PremiumProviderError):
    """Configured Premium provider is disabled or failed closed."""


class PremiumProvider(Protocol):
    def health(self) -> PremiumProviderHealth: ...

    async def subscription_status(
        self,
        request: PremiumProviderRequest,
    ) -> PremiumProviderResult: ...


class DisabledPremiumProvider:
    def health(self) -> PremiumProviderHealth:
        return PremiumProviderHealth(
            mode=PremiumProviderMode.DISABLED,
            available=False,
        )

    async def subscription_status(
        self,
        request: PremiumProviderRequest,
    ) -> PremiumProviderResult:
        del request
        raise PremiumProviderUnavailable("Premium provider unavailable")


class FakePremiumProvider:
    """Deterministic local/CI provider with no network or billing dependency."""

    def __init__(
        self,
        *,
        states: Mapping[uuid.UUID, SubscriptionState] | None = None,
    ) -> None:
        self._states = dict(states or {})
        self.requests: list[PremiumProviderRequest] = []

    def health(self) -> PremiumProviderHealth:
        return PremiumProviderHealth(
            mode=PremiumProviderMode.TEST,
            available=True,
        )

    async def subscription_status(
        self,
        request: PremiumProviderRequest,
    ) -> PremiumProviderResult:
        self.requests.append(request)
        return PremiumProviderResult(
            request_id=request.request_id,
            account_id=request.account_id,
            subscription_state=self._states.get(request.account_id, "inactive"),
        )


class PremiumProviderBoundary:
    """Timeout and integrity boundary around the configured Premium provider."""

    def __init__(
        self,
        provider: PremiumProvider,
        *,
        timeout_ms: int = PREMIUM_PROVIDER_TIMEOUT_MS,
    ) -> None:
        if not 10 <= timeout_ms <= 2_000:
            raise ValueError("Premium provider timeout is out of bounds")
        self._provider = provider
        self._timeout_seconds = timeout_ms / 1_000

    def health(self) -> PremiumProviderHealth:
        try:
            health = self._provider.health()
        except Exception:
            return PremiumProviderHealth(
                mode=PremiumProviderMode.DISABLED,
                available=False,
            )
        if health.mode not in {
            PremiumProviderMode.DISABLED,
            PremiumProviderMode.TEST,
        }:
            return PremiumProviderHealth(
                mode=PremiumProviderMode.DISABLED,
                available=False,
            )
        return health

    async def subscription_status(
        self,
        request: PremiumProviderRequest,
    ) -> PremiumProviderResult:
        result = await self._run(self._provider.subscription_status(request))
        if result.request_id != request.request_id:
            raise PremiumProviderUnavailable("Premium provider unavailable")
        if result.account_id != request.account_id:
            raise PremiumProviderUnavailable("Premium provider unavailable")
        if result.provider_mode != "test" or result.provider_version != "test-v1":
            raise PremiumProviderUnavailable("Premium provider unavailable")
        return result

    async def _run(
        self,
        operation: Awaitable[PremiumProviderResult],
    ) -> PremiumProviderResult:
        try:
            return await asyncio.wait_for(
                operation,
                timeout=self._timeout_seconds,
            )
        except Exception:
            raise PremiumProviderUnavailable("Premium provider unavailable") from None


def build_premium_provider(
    provider: Literal["disabled", "fake"] = "disabled",
    *,
    environment: Literal["local", "test", "field-test", "production"] = "local",
    states: Mapping[uuid.UUID, SubscriptionState] | None = None,
) -> PremiumProvider:
    if environment not in {"local", "test"} and provider != "disabled":
        raise PremiumProviderUnavailable("Premium provider unavailable")
    if provider == "disabled":
        return DisabledPremiumProvider()
    if provider == "fake":
        return FakePremiumProvider(states=states)
    raise PremiumProviderUnavailable("Premium provider unavailable")
