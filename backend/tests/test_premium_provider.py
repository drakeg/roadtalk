import asyncio
import uuid

import pytest
from pydantic import ValidationError

from app.premium.provider import (
    DisabledPremiumProvider,
    FakePremiumProvider,
    PremiumProviderBoundary,
    PremiumProviderHealth,
    PremiumProviderMode,
    PremiumProviderRequest,
    PremiumProviderResult,
    PremiumProviderUnavailable,
    build_premium_provider,
)


def test_disabled_provider_reports_unavailable_and_fails_closed() -> None:
    provider = DisabledPremiumProvider()
    assert provider.health() == PremiumProviderHealth(
        mode=PremiumProviderMode.DISABLED,
        available=False,
    )

    with pytest.raises(PremiumProviderUnavailable, match="Premium provider unavailable"):
        asyncio.run(
            provider.subscription_status(
                PremiumProviderRequest(
                    request_id=uuid.uuid4(),
                    account_id=uuid.uuid4(),
                )
            )
        )


def test_fake_provider_is_deterministic_and_provider_neutral() -> None:
    account_id = uuid.uuid4()
    request = PremiumProviderRequest(
        request_id=uuid.uuid4(),
        account_id=account_id,
    )
    provider = FakePremiumProvider(states={account_id: "active"})

    result = asyncio.run(provider.subscription_status(request))

    assert result == PremiumProviderResult(
        request_id=request.request_id,
        account_id=account_id,
        subscription_state="active",
    )
    assert provider.requests == [request]
    assert provider.health().mode == PremiumProviderMode.TEST


def test_request_and_result_contracts_are_closed() -> None:
    request = PremiumProviderRequest(
        request_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
    )
    result = PremiumProviderResult(
        request_id=request.request_id,
        account_id=request.account_id,
        subscription_state="inactive",
    )

    for value in (request, result):
        with pytest.raises(ValidationError):
            value.__class__.model_validate(
                {
                    **value.model_dump(),
                    "provider_secret": "attacker-controlled",
                }
            )


def test_boundary_rejects_mismatched_result_identity() -> None:
    request = PremiumProviderRequest(
        request_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
    )

    class MismatchedProvider(FakePremiumProvider):
        async def subscription_status(
            self,
            value: PremiumProviderRequest,
        ) -> PremiumProviderResult:
            return PremiumProviderResult(
                request_id=uuid.uuid4(),
                account_id=value.account_id,
                subscription_state="active",
            )

    with pytest.raises(
        PremiumProviderUnavailable,
        match="Premium provider unavailable",
    ):
        asyncio.run(
            PremiumProviderBoundary(MismatchedProvider()).subscription_status(request)
        )


def test_boundary_normalizes_provider_exceptions() -> None:
    request = PremiumProviderRequest(
        request_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
    )

    class BrokenProvider(FakePremiumProvider):
        async def subscription_status(
            self,
            value: PremiumProviderRequest,
        ) -> PremiumProviderResult:
            del value
            raise RuntimeError("provider-secret-detail")

    with pytest.raises(PremiumProviderUnavailable) as error:
        asyncio.run(
            PremiumProviderBoundary(BrokenProvider()).subscription_status(request)
        )
    assert "provider-secret-detail" not in str(error.value)


def test_builder_allows_fake_only_in_local_or_test_environments() -> None:
    assert isinstance(build_premium_provider(), DisabledPremiumProvider)
    assert isinstance(build_premium_provider("fake", environment="test"), FakePremiumProvider)

    with pytest.raises(
        PremiumProviderUnavailable,
        match="Premium provider unavailable",
    ):
        build_premium_provider("fake", environment="production")


def test_no_live_provider_configuration_is_exposed_by_contract() -> None:
    fields = set(PremiumProviderRequest.model_fields) | set(PremiumProviderResult.model_fields)
    forbidden = {
        "api_key",
        "provider_url",
        "checkout_url",
        "credential",
        "token",
        "access_token",
        "refresh_token",
        "webhook_secret",
        "payment_method",
    }
    assert fields.isdisjoint(forbidden)
