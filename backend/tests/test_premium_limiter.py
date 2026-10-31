import pytest

from app.premium.limiter import PremiumRateLimitError, PremiumStatusLimiter


def limiter(**overrides: int) -> PremiumStatusLimiter:
    values = {
        "account_limit": 10,
        "device_limit": 10,
        "peer_limit": 10,
        "window_seconds": 60,
        "max_buckets": 100,
    }
    values.update(overrides)
    return PremiumStatusLimiter(**values)


def test_account_device_and_peer_dimensions_are_independent() -> None:
    account = limiter(account_limit=1)
    account.check(peer="peer-a", account_id="account-a", device_id="device-a", now=1)
    with pytest.raises(PremiumRateLimitError):
        account.check(peer="peer-b", account_id="account-a", device_id="device-b", now=2)

    device = limiter(device_limit=1)
    device.check(peer="peer-a", account_id="account-a", device_id="device-a", now=1)
    with pytest.raises(PremiumRateLimitError):
        device.check(peer="peer-b", account_id="account-b", device_id="device-a", now=2)

    peer = limiter(peer_limit=1)
    peer.check(peer="peer-a", account_id="account-a", device_id="device-a", now=1)
    with pytest.raises(PremiumRateLimitError):
        peer.check(peer="peer-a", account_id="account-b", device_id="device-b", now=2)


def test_peer_identifier_is_hashed_and_error_is_generic() -> None:
    value = limiter(peer_limit=1)
    value.check(peer="198.51.100.10", account_id="a", device_id="d", now=1)

    with pytest.raises(PremiumRateLimitError) as limited:
        value.check(peer="198.51.100.10", account_id="b", device_id="e", now=2)

    assert str(limited.value) == "Premium request is temporarily unavailable."
    assert limited.value.retry_after == 59
    assert all("198.51.100.10" not in key_value for _, key_value in value._events)


def test_window_expiry_releases_capacity_and_storage_is_bounded() -> None:
    value = limiter(account_limit=1, max_buckets=3)
    value.check(peer="a", account_id="account-a", device_id="device-a", now=1)
    value.check(peer="b", account_id="account-a", device_id="device-b", now=61)
    assert len(value._events) <= 3
