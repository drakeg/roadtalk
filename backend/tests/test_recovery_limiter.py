import pytest

from app.recovery.limiter import RecoveryLimiter, RecoveryRateLimitError


def limiter() -> RecoveryLimiter:
    return RecoveryLimiter(
        attempt_limit=2,
        attempt_window_seconds=60,
        mutation_limit=1,
        mutation_window_seconds=120,
        max_buckets=20,
    )


def test_attempt_limits_cover_peer_device_and_selector_dimensions() -> None:
    control = limiter()
    control.check_attempt(
        peer="peer-a",
        installation_id="device-a",
        selector="selector-a",
        now=100.0,
    )
    control.check_attempt(
        peer="peer-a",
        installation_id="device-b",
        selector="selector-b",
        now=110.0,
    )

    with pytest.raises(RecoveryRateLimitError) as raised:
        control.check_attempt(
            peer="peer-a",
            installation_id="device-c",
            selector="selector-c",
            now=120.0,
        )

    assert raised.value.retry_after == 40
    control.check_attempt(
        peer="peer-a",
        installation_id="device-c",
        selector="selector-c",
        now=161.0,
    )


def test_mutation_limits_are_account_and_device_scoped() -> None:
    control = limiter()
    control.check_mutation(account_id="account-a", device_id="device-a", now=1.0)

    with pytest.raises(RecoveryRateLimitError):
        control.check_mutation(
            account_id="account-a",
            device_id="device-b",
            now=2.0,
        )

    with pytest.raises(RecoveryRateLimitError):
        control.check_mutation(
            account_id="account-b",
            device_id="device-a",
            now=2.0,
        )

    control.check_mutation(
        account_id="account-b",
        device_id="device-b",
        now=2.0,
    )
