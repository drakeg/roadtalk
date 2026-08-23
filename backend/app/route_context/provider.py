from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config import Settings


class RouteContextDirection(StrEnum):
    NORTH = "north"
    NORTHEAST = "northeast"
    EAST = "east"
    SOUTHEAST = "southeast"
    SOUTH = "south"
    SOUTHWEST = "southwest"
    WEST = "west"
    NORTHWEST = "northwest"
    STATIONARY = "stationary"
    UNKNOWN = "unknown"


class RouteContextConfidence(StrEnum):
    CONFIDENT = "confident"
    AMBIGUOUS = "ambiguous"


class RouteContextMatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    horizontal_accuracy_m: float = Field(gt=0, le=50_000)
    heading_degrees: float | None = Field(default=None, ge=0, lt=360)
    speed_mps: float | None = Field(default=None, ge=0, le=1_000)
    observed_at: datetime
    source_location_version: int = Field(ge=1)

    @field_validator("observed_at")
    @classmethod
    def observed_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        return value.astimezone(UTC)


class RouteContextMatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider_corridor_ref: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    direction: RouteContextDirection
    confidence: RouteContextConfidence
    source_location_version: int = Field(ge=1)
    provider_version: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$")
    policy_version: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$")
    matched_at: datetime
    expires_at: datetime

    @field_validator("matched_at", "expires_at")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("route-context timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def expiry_must_follow_match(self) -> RouteContextMatchResult:
        if self.expires_at <= self.matched_at:
            raise ValueError("expires_at must be after matched_at")
        return self


class RouteContextProviderError(RuntimeError):
    """Stable non-disclosing route-context provider failure."""


class RouteContextProviderUnavailable(RouteContextProviderError):
    """Provider could not produce a usable route context."""


class RouteContextProvider(Protocol):
    async def match(self, request: RouteContextMatchRequest) -> RouteContextMatchResult: ...


@dataclass(frozen=True, slots=True)
class FakeRouteContextFixture:
    provider_corridor_ref: str
    direction: RouteContextDirection
    confidence: RouteContextConfidence = RouteContextConfidence.CONFIDENT


class FakeRouteContextProvider:
    """Deterministic local/CI provider with no network or dataset dependency."""

    def __init__(
        self,
        fixtures: Mapping[tuple[float, float], FakeRouteContextFixture] | None = None,
        *,
        policy_version: str = "route-v1",
        ttl_seconds: int = 60,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._fixtures = dict(fixtures or {})
        self._policy_version = policy_version
        self._ttl_seconds = ttl_seconds
        self._clock = clock or (lambda: datetime.now(UTC))

    async def match(self, request: RouteContextMatchRequest) -> RouteContextMatchResult:
        key = (round(request.latitude, 5), round(request.longitude, 5))
        fixture = self._fixtures.get(key)
        if fixture is None:
            raise RouteContextProviderUnavailable("route context unavailable")

        matched_at = self._clock().astimezone(UTC)
        return RouteContextMatchResult(
            provider_corridor_ref=fixture.provider_corridor_ref,
            direction=fixture.direction,
            confidence=fixture.confidence,
            source_location_version=request.source_location_version,
            provider_version="fake-v1",
            policy_version=self._policy_version,
            matched_at=matched_at,
            expires_at=matched_at + timedelta(seconds=self._ttl_seconds),
        )


class DisabledRouteContextProvider:
    async def match(self, request: RouteContextMatchRequest) -> RouteContextMatchResult:
        del request
        raise RouteContextProviderUnavailable("route context unavailable")


class RouteContextMatcher:
    """Timeout and integrity boundary around any configured provider implementation."""

    def __init__(
        self,
        provider: RouteContextProvider,
        *,
        timeout_ms: int,
        max_ttl_seconds: int,
        expected_policy_version: str,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._provider = provider
        self._timeout_seconds = timeout_ms / 1_000
        self._max_ttl = timedelta(seconds=max_ttl_seconds)
        self._expected_policy_version = expected_policy_version
        self._clock = clock or (lambda: datetime.now(UTC))

    async def match(self, request: RouteContextMatchRequest) -> RouteContextMatchResult:
        try:
            result = await asyncio.wait_for(
                self._provider.match(request),
                timeout=self._timeout_seconds,
            )
        except Exception:
            raise RouteContextProviderUnavailable("route context unavailable") from None

        now = self._clock().astimezone(UTC)
        if result.source_location_version != request.source_location_version:
            raise RouteContextProviderUnavailable("route context unavailable")
        if result.policy_version != self._expected_policy_version:
            raise RouteContextProviderUnavailable("route context unavailable")
        if result.expires_at - result.matched_at > self._max_ttl:
            raise RouteContextProviderUnavailable("route context unavailable")
        if result.expires_at <= now:
            raise RouteContextProviderUnavailable("route context unavailable")
        return result


def build_route_context_provider(
    settings: Settings,
    *,
    fixtures: Mapping[tuple[float, float], FakeRouteContextFixture] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> RouteContextProvider:
    if settings.route_context_provider == "disabled":
        return DisabledRouteContextProvider()
    if settings.route_context_provider == "fake":
        return FakeRouteContextProvider(
            fixtures,
            policy_version=settings.route_context_policy_version,
            ttl_seconds=settings.route_context_ttl_seconds,
            clock=clock,
        )
    raise RouteContextProviderUnavailable("route context unavailable")
