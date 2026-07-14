import uuid

import pytest

from app.identity.callsigns import (
    CallsignAvailabilityLimiter,
    CallsignPolicyError,
    CallsignRateLimitError,
    validate_callsign,
)


@pytest.mark.parametrize(
    ("candidate", "display", "normalized"),
    [
        (" Road-Runner ", "Road-Runner", "road-runner"),
        ("NIGHT123", "NIGHT123", "night123"),
        ("Ｒoadie", "Roadie", "roadie"),
    ],
)
def test_callsign_normalization_is_deterministic(
    candidate: str,
    display: str,
    normalized: str,
) -> None:
    callsign = validate_callsign(candidate)

    assert callsign.display == display
    assert callsign.normalized == normalized


@pytest.mark.parametrize(
    ("candidate", "code"),
    [
        ("ab", "CALLSIGN_INVALID_LENGTH"),
        ("a" * 25, "CALLSIGN_INVALID_LENGTH"),
        ("-road", "CALLSIGN_INVALID_CHARACTERS"),
        ("road-", "CALLSIGN_INVALID_CHARACTERS"),
        ("road--runner", "CALLSIGN_INVALID_CHARACTERS"),
        ("road_runner", "CALLSIGN_INVALID_CHARACTERS"),
        ("rоad", "CALLSIGN_INVALID_CHARACTERS"),
        ("road talk", "CALLSIGN_INVALID_CHARACTERS"),
        ("admin", "CALLSIGN_RESERVED"),
        ("RoadTalk-Help", "CALLSIGN_RESERVED"),
        ("system-alert", "CALLSIGN_RESERVED"),
    ],
)
def test_callsign_policy_rejects_unsafe_values(candidate: str, code: str) -> None:
    with pytest.raises(CallsignPolicyError) as raised:
        validate_callsign(candidate)

    assert raised.value.code == code


def test_availability_limit_is_scoped_and_expires() -> None:
    account_id = uuid.uuid4()
    first_device = uuid.uuid4()
    second_device = uuid.uuid4()
    limiter = CallsignAvailabilityLimiter(limit=2, window_seconds=60)

    limiter.check(account_id=account_id, device_id=first_device, now=100.0)
    limiter.check(account_id=account_id, device_id=first_device, now=110.0)
    limiter.check(account_id=account_id, device_id=second_device, now=110.0)

    with pytest.raises(CallsignRateLimitError) as raised:
        limiter.check(account_id=account_id, device_id=first_device, now=120.0)

    assert raised.value.retry_after == 40
    limiter.check(account_id=account_id, device_id=first_device, now=161.0)


def test_availability_limiter_bounds_identity_buckets() -> None:
    limiter = CallsignAvailabilityLimiter(limit=1, window_seconds=60, max_buckets=2)

    limiter.check(account_id=uuid.uuid4(), device_id=uuid.uuid4(), now=1.0)
    limiter.check(account_id=uuid.uuid4(), device_id=uuid.uuid4(), now=1.0)
    limiter.check(account_id=uuid.uuid4(), device_id=uuid.uuid4(), now=1.0)

    assert len(limiter._events) == 2
