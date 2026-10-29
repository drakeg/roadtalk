from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.premium.contracts import EntitlementContext, EntitlementState


class RoadTalkFeature(StrEnum):
    BASELINE_COMMUNICATION = "baseline_communication"
    PREMIUM_EXPERIENCE = "premium_experience"


class FeatureClass(StrEnum):
    BASELINE = "baseline"
    PREMIUM = "premium"


FEATURE_POLICY = MappingProxyType(
    {
        RoadTalkFeature.BASELINE_COMMUNICATION: FeatureClass.BASELINE,
        RoadTalkFeature.PREMIUM_EXPERIENCE: FeatureClass.PREMIUM,
    }
)

# A server entitlement observation older than this is not trusted for a Premium
# allow; callers must re-read the server-owned lifecycle instead of reusing a
# cached context.
ENTITLEMENT_MAX_OBSERVATION_AGE = timedelta(minutes=5)
# Bounded tolerance for an entitlement observed slightly after the gate clock.
ENTITLEMENT_MAX_FUTURE_SKEW = timedelta(seconds=30)

PremiumGateReason = Literal[
    "baseline_allowed",
    "premium_entitled",
    "existing_authorization_required",
    "premium_entitlement_required",
    "premium_entitlement_stale",
    "premium_entitlement_account_mismatch",
]


class PremiumGateDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    account_id: uuid.UUID
    feature: RoadTalkFeature
    feature_class: FeatureClass
    allowed: bool
    reason: PremiumGateReason
    entitlement_state: EntitlementState | None = None
    observed_at: datetime
    server_authoritative: Literal[True] = True
    existing_authorization_unchanged: Literal[True] = True


def evaluate_feature_access(
    *,
    account_id: uuid.UUID,
    feature: RoadTalkFeature,
    existing_authorized: bool,
    entitlement: EntitlementContext | None,
    observed_at: datetime,
) -> PremiumGateDecision:
    observed = _as_utc(observed_at)
    feature_class = FEATURE_POLICY[feature]

    def decide(allowed: bool, reason: PremiumGateReason) -> PremiumGateDecision:
        return PremiumGateDecision(
            account_id=account_id,
            feature=feature,
            feature_class=feature_class,
            allowed=allowed,
            reason=reason,
            entitlement_state=entitlement.state if entitlement is not None else None,
            observed_at=observed,
        )

    if not existing_authorized:
        return decide(False, "existing_authorization_required")

    if feature_class == FeatureClass.BASELINE:
        return decide(True, "baseline_allowed")

    if entitlement is None:
        return decide(False, "premium_entitlement_required")

    if entitlement.account_id != account_id:
        return decide(False, "premium_entitlement_account_mismatch")

    # Lifecycle activation and renewal always carry an expiry, so an active
    # entitlement without one is malformed and must not grant open-ended access.
    if entitlement.state != "active" or entitlement.expires_at is None:
        return decide(False, "premium_entitlement_required")

    entitlement_observed = _as_utc(entitlement.observed_at)
    if (
        observed >= _as_utc(entitlement.expires_at)
        or entitlement_observed < observed - ENTITLEMENT_MAX_OBSERVATION_AGE
        or entitlement_observed > observed + ENTITLEMENT_MAX_FUTURE_SKEW
    ):
        return decide(False, "premium_entitlement_stale")

    return decide(True, "premium_entitled")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Premium feature gate requires an aware timestamp")
    return value.astimezone(UTC)
