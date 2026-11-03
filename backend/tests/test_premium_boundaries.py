from app.premium.boundaries import (
    SUPPORTED_PREMIUM_COMPATIBILITY,
    PremiumBoundaryDisposition,
    PremiumResponsibility,
    premium_live_responsibility_boundary,
)


def test_live_responsibilities_are_explicitly_outside_deterministic_scope() -> None:
    for responsibility in PremiumResponsibility:
        decision = premium_live_responsibility_boundary(responsibility)

        assert decision.responsibility == responsibility
        assert decision.disposition == PremiumBoundaryDisposition.LIVE_APPROVAL_REQUIRED
        assert decision.implemented_live is False
        assert decision.recurring_cost_usd == 0
        assert decision.requires_separate_approval is True


def test_compatibility_baseline_matches_supported_platform_contract() -> None:
    baseline = SUPPORTED_PREMIUM_COMPATIBILITY

    assert baseline.python_major_minor == "3.14"
    assert baseline.node_major == 26
    assert baseline.react_native_major_minor == "0.86"
    assert baseline.expo_sdk_major == 57
    assert baseline.premium_provider_modes == ("disabled", "test")
    assert baseline.live_payment_provider_enabled is False
    assert baseline.recurring_cost_usd == 0
