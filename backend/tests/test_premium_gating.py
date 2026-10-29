import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.premium.contracts import EntitlementContext, EntitlementState
from app.premium.gating import (
    ENTITLEMENT_MAX_FUTURE_SKEW,
    ENTITLEMENT_MAX_OBSERVATION_AGE,
    FEATURE_POLICY,
    FeatureClass,
    RoadTalkFeature,
    evaluate_feature_access,
)


def entitlement(
    *,
    account_id: uuid.UUID,
    state: EntitlementState = "active",
    expires_at: datetime | None = None,
    observed_at: datetime | None = None,
) -> EntitlementContext:
    return EntitlementContext(
        entitlement_id=uuid.uuid4(),
        account_id=account_id,
        entitlement="premium",
        state=state,
        observed_at=observed_at or datetime.now(UTC),
        expires_at=expires_at,
    )


def test_baseline_feature_remains_available_without_premium() -> None:
    account_id = uuid.uuid4()
    decision = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.BASELINE_COMMUNICATION,
        existing_authorized=True,
        entitlement=None,
        observed_at=datetime.now(UTC),
    )

    assert decision.allowed is True
    assert decision.feature_class == FeatureClass.BASELINE
    assert decision.reason == "baseline_allowed"
    assert decision.server_authoritative is True
    assert decision.existing_authorization_unchanged is True


def test_premium_feature_requires_active_server_entitlement() -> None:
    account_id = uuid.uuid4()
    now = datetime.now(UTC)

    denied = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=None,
        observed_at=now,
    )
    allowed = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=entitlement(
            account_id=account_id,
            expires_at=now + timedelta(days=30),
        ),
        observed_at=now,
    )

    assert denied.allowed is False
    assert denied.reason == "premium_entitlement_required"
    assert allowed.allowed is True
    assert allowed.reason == "premium_entitled"


def test_premium_never_creates_existing_roadtalk_authorization() -> None:
    account_id = uuid.uuid4()
    now = datetime.now(UTC)
    active = entitlement(
        account_id=account_id,
        expires_at=now + timedelta(days=30),
    )

    for feature in RoadTalkFeature:
        decision = evaluate_feature_access(
            account_id=account_id,
            feature=feature,
            existing_authorized=False,
            entitlement=active,
            observed_at=now,
        )
        assert decision.allowed is False
        assert decision.reason == "existing_authorization_required"


@pytest.mark.parametrize("state", ["inactive", "expired", "revoked"])
def test_non_active_entitlement_fails_closed(state: EntitlementState) -> None:
    account_id = uuid.uuid4()
    decision = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=entitlement(account_id=account_id, state=state),
        observed_at=datetime.now(UTC),
    )

    assert decision.allowed is False
    assert decision.reason == "premium_entitlement_required"


def test_expired_active_entitlement_is_treated_as_stale() -> None:
    account_id = uuid.uuid4()
    now = datetime.now(UTC)
    decision = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=entitlement(
            account_id=account_id,
            expires_at=now,
        ),
        observed_at=now,
    )

    assert decision.allowed is False
    assert decision.reason == "premium_entitlement_stale"


def test_entitlement_cannot_be_reused_for_another_account() -> None:
    account_id = uuid.uuid4()
    decision = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=entitlement(account_id=uuid.uuid4()),
        observed_at=datetime.now(UTC),
    )

    assert decision.allowed is False
    assert decision.reason == "premium_entitlement_account_mismatch"


def test_feature_policy_is_closed_and_auditable() -> None:
    assert FEATURE_POLICY == {
        RoadTalkFeature.BASELINE_COMMUNICATION: FeatureClass.BASELINE,
        RoadTalkFeature.PREMIUM_EXPERIENCE: FeatureClass.PREMIUM,
    }
    assert set(FEATURE_POLICY) == set(RoadTalkFeature)
    with pytest.raises(TypeError):
        FEATURE_POLICY[RoadTalkFeature.BASELINE_COMMUNICATION] = FeatureClass.PREMIUM  # type: ignore[index]


def test_active_entitlement_without_expiry_fails_closed() -> None:
    account_id = uuid.uuid4()
    decision = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=entitlement(account_id=account_id, expires_at=None),
        observed_at=datetime.now(UTC),
    )

    assert decision.allowed is False
    assert decision.reason == "premium_entitlement_required"


@pytest.mark.parametrize(
    "observation_offset",
    [
        -ENTITLEMENT_MAX_OBSERVATION_AGE - timedelta(seconds=1),
        ENTITLEMENT_MAX_FUTURE_SKEW + timedelta(seconds=1),
    ],
)
def test_stale_or_future_entitlement_observation_fails_closed(
    observation_offset: timedelta,
) -> None:
    account_id = uuid.uuid4()
    now = datetime.now(UTC)
    decision = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=entitlement(
            account_id=account_id,
            expires_at=now + timedelta(days=30),
            observed_at=now + observation_offset,
        ),
        observed_at=now,
    )

    assert decision.allowed is False
    assert decision.reason == "premium_entitlement_stale"


def test_entitlement_observation_within_bounds_is_accepted() -> None:
    account_id = uuid.uuid4()
    now = datetime.now(UTC)
    for offset in (-ENTITLEMENT_MAX_OBSERVATION_AGE, ENTITLEMENT_MAX_FUTURE_SKEW):
        decision = evaluate_feature_access(
            account_id=account_id,
            feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
            existing_authorized=True,
            entitlement=entitlement(
                account_id=account_id,
                expires_at=now + timedelta(days=30),
                observed_at=now + offset,
            ),
            observed_at=now,
        )
        assert decision.allowed is True


def test_decision_does_not_echo_entitlement_identity_or_expiry() -> None:
    account_id = uuid.uuid4()
    now = datetime.now(UTC)
    active = entitlement(account_id=account_id, expires_at=now + timedelta(days=30))
    decision = evaluate_feature_access(
        account_id=account_id,
        feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
        existing_authorized=True,
        entitlement=active,
        observed_at=now,
    )

    payload = decision.model_dump(mode="json")
    assert str(active.entitlement_id) not in str(payload)
    assert "expires_at" not in payload


def test_naive_observation_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="aware timestamp"):
        evaluate_feature_access(
            account_id=uuid.uuid4(),
            feature=RoadTalkFeature.PREMIUM_EXPERIENCE,
            existing_authorized=True,
            entitlement=None,
            observed_at=datetime(2026, 1, 1),
        )
