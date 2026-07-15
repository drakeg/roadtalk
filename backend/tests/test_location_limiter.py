import pytest

from app.location.limiter import LocationLimiter, LocationRateLimitError


def limiter(*, max_buckets: int = 20) -> LocationLimiter:
    return LocationLimiter(
        mutation_limit=2,
        mutation_window_seconds=60,
        nearby_read_limit=1,
        nearby_read_window_seconds=120,
        max_buckets=max_buckets,
    )


def test_mutation_limits_peer_account_and_device_dimensions() -> None:
    control = limiter()
    control.check_mutation(
        peer="peer-a",
        account_id="account-a",
        device_id="device-a",
        now=100,
    )
    control.check_mutation(
        peer="peer-a",
        account_id="account-b",
        device_id="device-b",
        now=110,
    )

    with pytest.raises(LocationRateLimitError) as raised:
        control.check_mutation(
            peer="peer-a",
            account_id="account-c",
            device_id="device-c",
            now=120,
        )

    assert raised.value.retry_after == 40
    control.check_mutation(
        peer="peer-a",
        account_id="account-c",
        device_id="device-c",
        now=161,
    )


def test_nearby_read_limits_account_device_and_peer_without_cross_action_sharing() -> None:
    control = limiter()
    control.check_mutation(
        peer="peer-a",
        account_id="account-a",
        device_id="device-a",
        now=1,
    )
    control.check_nearby_read(
        peer="peer-a",
        account_id="account-a",
        device_id="device-a",
        now=1,
    )

    with pytest.raises(LocationRateLimitError) as raised:
        control.check_nearby_read(
            peer="peer-b",
            account_id="account-a",
            device_id="device-b",
            now=2,
        )

    assert raised.value.retry_after == 119


def test_location_limiter_bounds_process_local_buckets() -> None:
    control = limiter(max_buckets=3)

    control.check_mutation(
        peer="peer-a",
        account_id="account-a",
        device_id="device-a",
        now=1,
    )
    control.check_mutation(
        peer="peer-b",
        account_id="account-b",
        device_id="device-b",
        now=1,
    )

    assert len(control._events) == 3
