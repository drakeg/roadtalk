import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from pydantic_core import ValidationError

from app.config import Settings
from app.route_context.provider import (
    DisabledRouteContextProvider,
    FakeRouteContextFixture,
    FakeRouteContextProvider,
    RouteContextConfidence,
    RouteContextDirection,
    RouteContextMatchRequest,
    RouteContextMatchResult,
    RouteContextMatcher,
    RouteContextProviderUnavailable,
    build_route_context_provider,
)

FIXED_NOW = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)


def request(*, source_location_version: int = 7) -> RouteContextMatchRequest:
    return RouteContextMatchRequest(
        latitude=40.12345,
        longitude=-76.54321,
        horizontal_accuracy_m=12.5,
        heading_degrees=91.0,
        speed_mps=24.0,
        observed_at=FIXED_NOW - timedelta(seconds=1),
        source_location_version=source_location_version,
    )


def test_request_is_exact_minimized_and_timezone_aware() -> None:
    sample = request()
    assert set(sample.model_dump()) == {
        "latitude",
        "longitude",
        "horizontal_accuracy_m",
        "heading_degrees",
        "speed_mps",
        "observed_at",
        "source_location_version",
    }

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RouteContextMatchRequest.model_validate({**sample.model_dump(), "road_name": "forbidden"})

    with pytest.raises(ValidationError, match="timezone-aware"):
        RouteContextMatchRequest(
            latitude=40,
            longitude=-76,
            horizontal_accuracy_m=10,
            observed_at=datetime(2026, 8, 22, 12, 0),
            source_location_version=1,
        )


def test_fake_provider_is_deterministic_and_network_free() -> None:
    async def exercise() -> None:
        fixture = FakeRouteContextFixture(
            provider_corridor_ref="fixture-corridor-17",
            direction=RouteContextDirection.EAST,
        )
        provider = FakeRouteContextProvider(
            {(40.12345, -76.54321): fixture},
            clock=lambda: FIXED_NOW,
        )
        result = await provider.match(request())

        assert result.provider_corridor_ref == "fixture-corridor-17"
        assert result.direction is RouteContextDirection.EAST
        assert result.confidence is RouteContextConfidence.CONFIDENT
        assert result.source_location_version == 7
        assert result.provider_version == "fake-v1"
        assert result.policy_version == "route-v1"
        assert result.expires_at - result.matched_at == timedelta(seconds=60)

        with pytest.raises(RouteContextProviderUnavailable, match="route context unavailable"):
            await provider.match(
                request().model_copy(update={"latitude": 41.0, "longitude": -77.0})
            )

    asyncio.run(exercise())


def test_result_rejects_invalid_corridor_direction_expiry_and_extra_payload() -> None:
    valid = {
        "provider_corridor_ref": "corridor-1",
        "direction": "north",
        "confidence": "confident",
        "source_location_version": 1,
        "provider_version": "fake-v1",
        "policy_version": "route-v1",
        "matched_at": FIXED_NOW,
        "expires_at": FIXED_NOW + timedelta(seconds=30),
    }

    with pytest.raises(ValidationError):
        RouteContextMatchResult.model_validate({**valid, "provider_corridor_ref": "road name / 1"})
    with pytest.raises(ValidationError):
        RouteContextMatchResult.model_validate({**valid, "direction": "forward"})
    with pytest.raises(ValidationError, match="expires_at must be after"):
        RouteContextMatchResult.model_validate({**valid, "expires_at": FIXED_NOW})
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RouteContextMatchResult.model_validate({**valid, "raw_provider_payload": {"x": 1}})


def test_matcher_enforces_source_policy_ttl_and_freshness_without_disclosure() -> None:
    class StaticProvider:
        def __init__(self, result: RouteContextMatchResult) -> None:
            self.result = result

        async def match(self, _: RouteContextMatchRequest) -> RouteContextMatchResult:
            return self.result

    async def exercise() -> None:
        base = RouteContextMatchResult(
            provider_corridor_ref="sensitive-provider-corridor",
            direction=RouteContextDirection.NORTH,
            confidence=RouteContextConfidence.CONFIDENT,
            source_location_version=7,
            provider_version="fake-v1",
            policy_version="route-v1",
            matched_at=FIXED_NOW,
            expires_at=FIXED_NOW + timedelta(seconds=30),
        )

        cases = (
            base.model_copy(update={"source_location_version": 8}),
            base.model_copy(update={"policy_version": "wrong-policy"}),
            base.model_copy(update={"expires_at": FIXED_NOW + timedelta(seconds=61)}),
            base.model_copy(
                update={
                    "matched_at": FIXED_NOW - timedelta(seconds=60),
                    "expires_at": FIXED_NOW - timedelta(seconds=1),
                }
            ),
        )
        for invalid in cases:
            matcher = RouteContextMatcher(
                StaticProvider(invalid),
                timeout_ms=100,
                max_ttl_seconds=60,
                expected_policy_version="route-v1",
                clock=lambda: FIXED_NOW,
            )
            with pytest.raises(RouteContextProviderUnavailable) as exc_info:
                await matcher.match(request())
            assert str(exc_info.value) == "route context unavailable"
            assert "sensitive-provider-corridor" not in str(exc_info.value)

    asyncio.run(exercise())


def test_matcher_times_out_and_masks_unexpected_provider_errors() -> None:
    class SlowProvider:
        async def match(self, _: RouteContextMatchRequest) -> RouteContextMatchResult:
            await asyncio.sleep(0.05)
            raise AssertionError("unreachable")

    class ExplodingProvider:
        async def match(self, _: RouteContextMatchRequest) -> RouteContextMatchResult:
            raise RuntimeError("sensitive raw provider payload")

    async def exercise() -> None:
        for provider, timeout_ms in ((SlowProvider(), 10), (ExplodingProvider(), 100)):
            matcher = RouteContextMatcher(
                provider,
                timeout_ms=timeout_ms,
                max_ttl_seconds=60,
                expected_policy_version="route-v1",
                clock=lambda: FIXED_NOW,
            )
            with pytest.raises(RouteContextProviderUnavailable) as exc_info:
                await matcher.match(request())
            assert str(exc_info.value) == "route context unavailable"
            assert "sensitive" not in str(exc_info.value)

    asyncio.run(exercise())


def test_route_context_provider_configuration_is_local_ci_only() -> None:
    disabled = Settings(environment="test")
    assert disabled.route_context_provider == "disabled"
    assert isinstance(build_route_context_provider(disabled), DisabledRouteContextProvider)

    fake_settings = Settings(environment="test", route_context_provider="fake")
    assert isinstance(build_route_context_provider(fake_settings), FakeRouteContextProvider)

    with pytest.raises(ValidationError):
        Settings(environment="test", route_context_provider="osrm")  # type: ignore[arg-type]
    with pytest.raises(ValidationError, match="must remain disabled"):
        Settings(environment="production", route_context_provider="fake")
    with pytest.raises(ValidationError, match="must remain disabled"):
        Settings(environment="field-test", route_context_provider="fake")


def test_route_context_ttl_cannot_outlive_accepted_location() -> None:
    with pytest.raises(ValidationError, match="must not exceed location_usable_ttl_seconds"):
        Settings(
            environment="test",
            location_usable_ttl_seconds=30,
            route_context_ttl_seconds=60,
        )
