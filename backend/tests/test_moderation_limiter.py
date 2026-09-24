import pytest

from app.moderation.limiter import ModerationRateLimitError, ModerationReportLimiter


def limiter(**overrides: int) -> ModerationReportLimiter:
    values = {
        "account_limit": 10,
        "device_limit": 10,
        "peer_limit": 10,
        "event_limit": 10,
        "window_seconds": 60,
        "max_buckets": 100,
    }
    values.update(overrides)
    return ModerationReportLimiter(**values)


def test_report_replay_is_bounded_and_event_key_is_hashed() -> None:
    value = limiter(event_limit=2)
    for now in (1.0, 2.0):
        value.check(
            peer="peer-a",
            account_id="account-a",
            device_id="device-a",
            event_key="report-key-a",
            now=now,
        )

    with pytest.raises(ModerationRateLimitError) as limited:
        value.check(
            peer="peer-a",
            account_id="account-a",
            device_id="device-a",
            event_key="report-key-a",
            now=3.0,
        )

    assert str(limited.value) == "Moderation request is temporarily unavailable."
    assert limited.value.retry_after == 58
    assert all("report-key-a" not in key_value for _, key_value in value._events)


def test_account_device_and_peer_dimensions_are_independent() -> None:
    account = limiter(account_limit=1)
    account.check(peer="a", account_id="account-a", device_id="device-a", event_key="a", now=1)
    with pytest.raises(ModerationRateLimitError):
        account.check(peer="b", account_id="account-a", device_id="device-b", event_key="b", now=2)

    device = limiter(device_limit=1)
    device.check(peer="a", account_id="account-a", device_id="device-a", event_key="a", now=1)
    with pytest.raises(ModerationRateLimitError):
        device.check(peer="b", account_id="account-b", device_id="device-a", event_key="b", now=2)

    peer = limiter(peer_limit=1)
    peer.check(peer="a", account_id="account-a", device_id="device-a", event_key="a", now=1)
    with pytest.raises(ModerationRateLimitError):
        peer.check(peer="a", account_id="account-b", device_id="device-b", event_key="b", now=2)


def test_window_expiry_releases_capacity_and_bucket_storage_is_bounded() -> None:
    value = limiter(account_limit=1, max_buckets=4)
    value.check(peer="a", account_id="account-a", device_id="device-a", event_key="a", now=1)
    value.check(peer="b", account_id="account-a", device_id="device-b", event_key="b", now=61)
    assert len(value._events) <= 4
