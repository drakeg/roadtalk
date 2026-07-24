import pytest

from app.ptt.limiter import PttLimiter, PttRateLimitError


def test_receive_limiter_is_bounded_across_peer_account_and_device() -> None:
    limiter = PttLimiter(receive_limit=1, receive_window_seconds=60, max_buckets=3)
    limiter.check_receive(peer="peer-a", account_id="account-a", device_id="device-a", now=1)

    with pytest.raises(PttRateLimitError) as limited:
        limiter.check_receive(
            peer="peer-a",
            account_id="account-a",
            device_id="device-a",
            now=2,
        )

    assert limited.value.retry_after == 59
    limiter.check_receive(peer="peer-a", account_id="account-a", device_id="device-a", now=61)
    assert len(limiter._events) <= 3
