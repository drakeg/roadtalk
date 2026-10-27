from __future__ import annotations

import uuid
from datetime import UTC, datetime
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


class PremiumGateDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    account_id: uuid.UUID
    feature: RoadTalkFeature
    feature_class: FeatureClass
    allowed: bool
    reason: Literal[
        "baseline_allowed",
        "premium_entitled",
        "existing_authorization_required",
        "premium_entitlement_required",
        "premium_entitlement_stale",
        "premium_entitlement_account_mismatch",
    ]
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

    if not existing_authorized:
        return _decision(
            account_id=account_id,
            feature=feature,
            feature_class=feature_class,
            allowed=False,
            reason="existing_authorization_required",
            entitlement=entitlement,
            observed_at=observed,
        )

    if feature_class == FeatureClass.BASELINE:
        return _decision(
            account_id=account_id,
            feature=feature,
            feature_class=feature_class,
            allowed=True,
            reason="baseline_allowed",
            entitlement=entitlement,
            observed_at=observed,
        )

    if entitlement is None:
        return _decision(
            account_id=account_id,
            feature=feature,
            feature_class=feature_class,
            allowed=False,
            reason="premium_entitlement_required",
            entitlement=None,
            observed_at=observed,
        )

    if entitlement.account_id != account_id:
        return _decision(
            account_id=account_id,
            feature=feature,
            feature_class=feature_class,
            allowed=False,
            reason="premium_entitlement_account_mismatch",
            entitlement=entitlement,
            observed_at=observed,
        )

    if entitlement.state != "active":
        return _decision(
            account_id=account_id,
            feature=feature,
            feature_class=feature_class,
            allowed=False,
            reason="premium_entitlement_required",
            entitlement=entitlement,
            observed_at=observed,
        )

    if entitlement.expires_at is not None and observed >= _as_utc(entitlement.expires_at):
        return _decision(
            account_id=account_id,
            feature=feature,
            feature_class=feature_class,
            allowed=False,
            reason="premium_entitlement_stale",
            entitlement=entitlement,
            observed_at=observed,
        )

    return _decision(
        account_id=account_id,
        feature=feature,
        feature_class=feature_class,
        allowed=True,
        reason="premium_entitled",
        entitlement=entitlement,
        observed_at=observed,
    )


def _decision(
    *,
    account_id: uuid.UUID,
    feature: RoadTalkFeature,
    feature_class: FeatureClass,
    allowed: bool,
    reason: Literal[
        "baseline_allowed",
        "premium_entitled",
        "existing_authorization_required",
        "premium_entitlement_required",
        "premium_entitlement_stale",
        "premium_entitlement_account_mismatch",
    ],
    entitlement: EntitlementContext | None,
    observed_at: datetime,
) -> PremiumGateDecision:
    return PremiumGateDecision(
        account_id=account_id,
        feature=feature,
        feature_class=feature_class,
        allowed=allowed,
        reason=reason,
        entitlement_state=entitlement.state if entitlement is not None else None,
        observed_at=observed_at,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Premium feature gate requires an aware timestamp")
    return value.astimezone(UTC)
