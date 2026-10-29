import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.premium.contracts import SubscriptionState
from app.premium.gating import ENTITLEMENT_MAX_OBSERVATION_AGE
from app.premium.provider import (
    DisabledPremiumProvider,
    FakePremiumProvider,
    PremiumProviderBoundary,
    PremiumProviderHealth,
    PremiumProviderMode,
    PremiumProviderRequest,
    PremiumProviderResult,
    PremiumProviderUnavailable,
)
from app.premium.status import SUBSCRIPTION_ENTITLEMENT, PremiumStatus, read_premium_status

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)


def _status(
    provider: object,
    account_id: uuid.UUID | None = None,
) -> PremiumStatus:
    return asyncio.run(
        read_premium_status(
            PremiumProviderBoundary(provider),  # type: ignore[arg-type]
            account_id=account_id or uuid.uuid4(),
            now=NOW,
        )
    )


def test_disabled_provider_reports_free_without_contacting_provider() -> None:
    status = _status(DisabledPremiumProvider())

    assert status.availability == "provider_disabled"
    assert status.provider_mode == "disabled"
    assert status.tier == "free"
    assert status.entitlement_state is None
    assert status.premium_experience_allowed is False
    assert status.reason == "premium_entitlement_required"
    assert status.checkout_available is False


@pytest.mark.parametrize(
    ("subscription_state", "allowed"),
    [
        ("inactive", False),
        ("active", True),
        ("grace", True),
        ("canceled", True),
        ("expired", False),
        ("revoked", False),
    ],
)
def test_subscription_state_maps_through_the_central_gate(
    subscription_state: SubscriptionState,
    allowed: bool,
) -> None:
    account_id = uuid.uuid4()
    status = _status(
        FakePremiumProvider(states={account_id: subscription_state}),
        account_id,
    )

    assert status.availability == "available"
    assert status.provider_mode == "test"
    assert status.entitlement_state == SUBSCRIPTION_ENTITLEMENT[subscription_state]
    assert status.premium_experience_allowed is allowed
    assert status.tier == ("premium" if allowed else "free")
    assert status.reason == ("premium_entitled" if allowed else "premium_entitlement_required")


def test_every_subscription_state_has_an_entitlement_mapping() -> None:
    assert set(SUBSCRIPTION_ENTITLEMENT) == set(SubscriptionState.__args__)  # type: ignore[attr-defined]


def test_unknown_account_defaults_to_free() -> None:
    status = _status(FakePremiumProvider(states={uuid.uuid4(): "active"}))

    assert status.tier == "free"
    assert status.entitlement_state == "inactive"


def test_status_is_short_lived_and_server_stamped() -> None:
    status = _status(FakePremiumProvider())

    assert status.observed_at == NOW
    assert status.valid_until == NOW + ENTITLEMENT_MAX_OBSERVATION_AGE
    assert status.valid_until - status.observed_at <= timedelta(minutes=5)
    assert status.server_authoritative is True
    assert status.communication_authorization_unchanged is True


class _FailingProvider:
    def health(self) -> PremiumProviderHealth:
        return PremiumProviderHealth(mode=PremiumProviderMode.TEST, available=True)

    async def subscription_status(self, request: PremiumProviderRequest) -> PremiumProviderResult:
        raise PremiumProviderUnavailable("secret-provider-detail sk_live_example")


class _CrossAccountProvider(_FailingProvider):
    async def subscription_status(self, request: PremiumProviderRequest) -> PremiumProviderResult:
        return PremiumProviderResult(
            request_id=request.request_id,
            account_id=uuid.uuid4(),
            subscription_state="active",
        )


@pytest.mark.parametrize("provider", [_FailingProvider(), _CrossAccountProvider()])
def test_provider_failure_is_generic_and_fails_closed(provider: object) -> None:
    status = _status(provider)

    assert status.availability == "provider_unavailable"
    assert status.premium_experience_allowed is False
    assert status.tier == "free"
    assert status.entitlement_state is None
    assert "secret" not in status.model_dump_json()
    assert "sk_live" not in status.model_dump_json()


def test_status_payload_is_closed_and_privacy_bounded() -> None:
    status = _status(FakePremiumProvider())
    payload = status.model_dump(mode="json")

    assert set(payload) == {
        "availability",
        "provider_mode",
        "tier",
        "entitlement_state",
        "premium_experience_allowed",
        "reason",
        "observed_at",
        "valid_until",
        "checkout_available",
        "server_authoritative",
        "communication_authorization_unchanged",
    }
    assert PremiumStatus.model_config.get("extra") == "forbid"


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="aware timestamp"):
        asyncio.run(
            read_premium_status(
                PremiumProviderBoundary(FakePremiumProvider()),
                account_id=uuid.uuid4(),
                now=datetime(2026, 10, 29),
            )
        )
