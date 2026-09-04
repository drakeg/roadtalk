import pytest

from app.notifications.limiter import UrgentAlertLimiter, UrgentAlertRateLimitError


def limiter(**overrides: int) -> UrgentAlertLimiter:
    values = {
        "account_limit": 10,
        "device_limit": 10,
        "peer_limit": 10,
        "event_limit": 10,
        "window_seconds": 60,
        "max_buckets": 100,
    }
    values.update(overrides)
    return UrgentAlertLimiter(**values)


def test_event_retries_are_bounded_without_exposing_recipient_state() -> None:
    value = limiter(event_limit=2)
    for now in (1.0, 2.0):
        value.check(
            peer="peer-a",
            account_id="account-a",
            device_id="device-a",
            event_key="event-a",
            now=now,
        )

    with pytest.raises(UrgentAlertRateLimitError) as limited:
        value.check(
            peer="peer-a",
            account_id="account-a",
            device_id="device-a",
            event_key="event-a",
            now=3.0,
        )

    assert str(limited.value) == "Urgent alert is temporarily unavailable."
    assert limited.value.retry_after == 58
    assert all("event-a" not in key_value for _, key_value in value._events)


def test_account_device_and_peer_dimensions_are_independent() -> None:
    account = limiter(account_limit=1)
    account.check(peer="peer-a", account_id="account-a", device_id="device-a", event_key="a", now=1)
    with pytest.raises(UrgentAlertRateLimitError):
        account.check(
            peer="peer-b", account_id="account-a", device_id="device-b", event_key="b", now=2
        )

    device = limiter(device_limit=1)
    device.check(peer="peer-a", account_id="account-a", device_id="device-a", event_key="a", now=1)
    with pytest.raises(UrgentAlertRateLimitError):
        device.check(
            peer="peer-b", account_id="account-b", device_id="device-a", event_key="b", now=2
        )

    peer = limiter(peer_limit=1)
    peer.check(peer="peer-a", account_id="account-a", device_id="device-a", event_key="a", now=1)
    with pytest.raises(UrgentAlertRateLimitError):
        peer.check(
            peer="peer-a", account_id="account-b", device_id="device-b", event_key="b", now=2
        )


def test_expired_buckets_release_capacity_and_storage_stays_bounded() -> None:
    value = limiter(account_limit=1, max_buckets=4)
    value.check(peer="peer-a", account_id="account-a", device_id="device-a", event_key="a", now=1)
    value.check(peer="peer-b", account_id="account-a", device_id="device-b", event_key="b", now=61)
    assert len(value._events) <= 4
