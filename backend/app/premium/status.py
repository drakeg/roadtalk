"""Server-authoritative Premium status for the browser and mobile experiences."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.premium.contracts import (
    EntitlementContext,
    EntitlementState,
    PremiumTier,
    SubscriptionState,
)
from app.premium.gating import (
    ENTITLEMENT_MAX_OBSERVATION_AGE,
    PremiumGateReason,
    RoadTalkFeature,
    evaluate_feature_access,
)
from app.premium.provider import (
    PremiumProviderBoundary,
    PremiumProviderError,
    PremiumProviderMode,
    PremiumProviderRequest,
)

PremiumAvailability = Literal["available", "provider_disabled", "provider_unavailable"]

# Cancellation keeps entitlement through the already-authorized period and a
# grace period keeps the subscription in effect, so both map to an active
# entitlement. Every other state grants nothing.
SUBSCRIPTION_ENTITLEMENT = MappingProxyType[SubscriptionState, EntitlementState](
    {
        "inactive": "inactive",
        "active": "active",
        "grace": "active",
        "canceled": "active",
        "expired": "expired",
        "revoked": "revoked",
    }
)


class PremiumStatus(BaseModel):
    """Closed status contract. It never carries provider, payment or location data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    availability: PremiumAvailability
    provider_mode: Literal["disabled", "test"]
    tier: PremiumTier
    entitlement_state: EntitlementState | None
    premium_experience_allowed: bool
    reason: PremiumGateReason
    observed_at: datetime
    valid_until: datetime
    checkout_available: Literal[False] = False
    server_authoritative: Literal[True] = True
    communication_authorization_unchanged: Literal[True] = True


async def read_premium_status(
    boundary: PremiumProviderBoundary,
    *,
    account_id: uuid.UUID,
    now: datetime,
) -> PremiumStatus:
    """Read Premium status for an already-authenticated account.

    The caller's authenticated session is the existing RoadTalk authorization for
    reading the caller's own Premium status; this function never widens it.
    """

    if now.tzinfo is None:
        raise ValueError("Premium status requires an aware timestamp")
    observed = now.astimezone(UTC)
    health = boundary.health()

    if health.mode is PremiumProviderMode.DISABLED or not health.available:
        return _status(
            account_id=account_id,
            availability="provider_disabled",
            provider_mode="disabled",
            entitlement=None,
            observed=observed,
        )

    try:
        result = await boundary.subscription_status(
            PremiumProviderRequest(request_id=uuid.uuid4(), account_id=account_id)
        )
    except PremiumProviderError:
        return _status(
            account_id=account_id,
            availability="provider_unavailable",
            provider_mode="test",
            entitlement=None,
            observed=observed,
        )

    # A provider observation is trusted only for the gate's observation window;
    # clients must re-read after valid_until instead of keeping cached Premium.
    entitlement = EntitlementContext(
        entitlement_id=uuid.uuid4(),
        account_id=account_id,
        entitlement="premium",
        state=SUBSCRIPTION_ENTITLEMENT[result.subscription_state],
        observed_at=observed,
        expires_at=observed + ENTITLEMENT_MAX_OBSERVATION_AGE,
    )
    return _status(
        account_id=account_id,
        availability="available",
        provider_mode="test",
        entitlement=entitlement,
        observed=observed,
    )


def _status(
    *,
    account_id: uuid.UUID,
    availability: PremiumAvailability,
    provider_mode: Literal["disabled", "test"],
    entitlement: EntitlementContext | None,
    observed: datetime,
) -> PremiumStatus:
    decision = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=entitlement,
        observed_at=observed,
    )
    return PremiumStatus(
        availability=availability,
        provider_mode=provider_mode,
        tier="premium" if decision.allowed else "free",
        entitlement_state=decision.entitlement_state,
        premium_experience_allowed=decision.allowed,
        reason=decision.reason,
        observed_at=observed,
        valid_until=observed + ENTITLEMENT_MAX_OBSERVATION_AGE,
    )
