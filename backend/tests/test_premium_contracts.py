import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.premium.contracts import (
    PROHIBITED_PREMIUM_FIELDS,
    EntitlementContext,
    PremiumAccountContext,
    SubscriptionContext,
)


def test_premium_account_context_is_closed_and_server_authoritative() -> None:
    context = PremiumAccountContext(account_id=uuid.uuid4(), tier="premium")
    assert context.server_authoritative is True
    assert context.authorization_source == "existing_roadtalk_authorization"

    with pytest.raises(ValidationError):
        PremiumAccountContext.model_validate(
            {**context.model_dump(), "server_authoritative": False}
        )
    with pytest.raises(ValidationError):
        PremiumAccountContext.model_validate(
            {**context.model_dump(), "authorization_source": "premium"}
        )


def test_subscription_context_rejects_live_provider_mode() -> None:
    context = SubscriptionContext(
        subscription_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        state="active",
        provider_mode="test",
        observed_at=datetime.now(UTC),
    )
    assert context.provider_mode == "test"

    with pytest.raises(ValidationError):
        SubscriptionContext.model_validate(
            {**context.model_dump(), "provider_mode": "live"}
        )


def test_entitlement_cannot_claim_communication_authorization() -> None:
    context = EntitlementContext(
        entitlement_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        entitlement="premium",
        state="active",
        observed_at=datetime.now(UTC),
    )
    assert context.communication_authorization_unchanged is True
    assert context.authorization_source == "existing_roadtalk_authorization"

    with pytest.raises(ValidationError):
        EntitlementContext.model_validate(
            {**context.model_dump(), "communication_authorization_unchanged": False}
        )


@pytest.mark.parametrize(
    "state",
    ["inactive", "active", "grace", "canceled", "expired", "revoked"],
)
def test_subscription_states_are_bounded(state: str) -> None:
    SubscriptionContext(
        subscription_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        state=state,
        observed_at=datetime.now(UTC),
    )

    with pytest.raises(ValidationError):
        SubscriptionContext(
            subscription_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            state="custom",
            observed_at=datetime.now(UTC),
        )


def test_premium_contracts_reject_sensitive_overposting() -> None:
    now = datetime.now(UTC)
    values = (
        PremiumAccountContext(account_id=uuid.uuid4(), tier="premium"),
        SubscriptionContext(
            subscription_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            state="active",
            observed_at=now,
        ),
        EntitlementContext(
            entitlement_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            entitlement="premium",
            state="active",
            observed_at=now,
        ),
    )

    for value in values:
        for field in sorted(PROHIBITED_PREMIUM_FIELDS):
            with pytest.raises(ValidationError):
                value.__class__.model_validate(
                    {**value.model_dump(), field: "attacker-controlled"}
                )


def test_tiers_are_bounded() -> None:
    PremiumAccountContext(account_id=uuid.uuid4(), tier="free")
    PremiumAccountContext(account_id=uuid.uuid4(), tier="premium")

    with pytest.raises(ValidationError):
        PremiumAccountContext(account_id=uuid.uuid4(), tier="enterprise")
