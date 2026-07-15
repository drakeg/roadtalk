import math
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.config import Settings
from app.location.quality import (
    ExistingLocation,
    LocationPolicy,
    LocationPolicyError,
    LocationSample,
    evaluate_location_sample,
    policy_from_settings,
)


def policy() -> LocationPolicy:
    return LocationPolicy(
        version="location-v1",
        max_sample_age_seconds=60,
        max_future_seconds=10,
        max_usable_accuracy_m=100,
        max_retained_accuracy_m=1_000,
        max_reported_speed_mps=100,
        max_plausible_speed_mps=100,
        plausibility_slack_m=250,
        usable_ttl_seconds=120,
        degraded_ttl_seconds=60,
        cross_device_newer_seconds=1,
    )


def sample(now: datetime, **overrides: object) -> LocationSample:
    values: dict[str, object] = {
        "latitude": 40.0,
        "longitude": -75.0,
        "observed_at": now,
        "horizontal_accuracy_m": 10.0,
        "heading_deg": 90.0,
        "speed_mps": 5.0,
        "client_sequence": 1,
        "consent_policy_version": "location-v1",
    }
    values.update(overrides)
    return LocationSample(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"latitude": 91.0}, "LOCATION_COORDINATES_INVALID"),
        ({"longitude": -181.0}, "LOCATION_COORDINATES_INVALID"),
        ({"latitude": math.nan}, "LOCATION_COORDINATES_INVALID"),
        ({"horizontal_accuracy_m": -1.0}, "LOCATION_ACCURACY_UNUSABLE"),
        ({"horizontal_accuracy_m": 1_001.0}, "LOCATION_ACCURACY_UNUSABLE"),
        ({"heading_deg": 360.0}, "LOCATION_HEADING_INVALID"),
        ({"heading_deg": math.inf}, "LOCATION_HEADING_INVALID"),
        ({"speed_mps": -1.0}, "LOCATION_SPEED_INVALID"),
        ({"speed_mps": 101.0}, "LOCATION_SPEED_INVALID"),
        ({"client_sequence": 0}, "LOCATION_SEQUENCE_INVALID"),
        ({"consent_policy_version": "old-policy"}, "LOCATION_POLICY_MISMATCH"),
    ],
)
def test_invalid_location_fields_fail_with_stable_non_disclosing_codes(
    overrides: dict[str, object],
    code: str,
) -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)

    with pytest.raises(LocationPolicyError) as raised:
        evaluate_location_sample(
            sample(now, **overrides),
            source_device_id=uuid.uuid4(),
            policy=policy(),
            now=now,
        )

    assert raised.value.code == code
    assert "40.0" not in raised.value.detail
    assert "-75.0" not in raised.value.detail


def test_time_policy_rejects_naive_future_and_stale_samples() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)
    cases = [
        (replace(sample(now), observed_at=now.replace(tzinfo=None)), "LOCATION_TIME_INVALID"),
        (
            replace(sample(now), observed_at=now + timedelta(seconds=11)),
            "LOCATION_TIME_INVALID",
        ),
        (
            replace(sample(now), observed_at=now - timedelta(seconds=61)),
            "LOCATION_SAMPLE_STALE",
        ),
    ]

    for candidate, code in cases:
        with pytest.raises(LocationPolicyError) as raised:
            evaluate_location_sample(
                candidate,
                source_device_id=uuid.uuid4(),
                policy=policy(),
                now=now,
            )
        assert raised.value.code == code


def test_accuracy_selects_bounded_usable_or_degraded_expiry() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)
    device_id = uuid.uuid4()

    usable = evaluate_location_sample(
        sample(now, horizontal_accuracy_m=100.0),
        source_device_id=device_id,
        policy=policy(),
        now=now,
    )
    degraded = evaluate_location_sample(
        sample(now, horizontal_accuracy_m=100.1),
        source_device_id=device_id,
        policy=policy(),
        now=now,
    )

    assert usable.quality_state == "usable"
    assert usable.expires_at == now + timedelta(seconds=120)
    assert degraded.quality_state == "degraded"
    assert degraded.expires_at == now + timedelta(seconds=60)


def test_same_device_requires_newer_sequence_and_observation() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)
    device_id = uuid.uuid4()
    existing = ExistingLocation(
        source_device_id=device_id,
        latitude=40.0,
        longitude=-75.0,
        observed_at=now - timedelta(seconds=10),
        horizontal_accuracy_m=10,
        client_sequence=4,
    )

    for candidate in (
        sample(now, client_sequence=4),
        sample(now - timedelta(seconds=10), client_sequence=5),
    ):
        with pytest.raises(LocationPolicyError) as raised:
            evaluate_location_sample(
                candidate,
                source_device_id=device_id,
                policy=policy(),
                now=now,
                existing=existing,
            )
        assert raised.value.code == "LOCATION_SAMPLE_OUT_OF_ORDER"

    accepted = evaluate_location_sample(
        sample(now, client_sequence=5),
        source_device_id=device_id,
        policy=policy(),
        now=now,
        existing=existing,
    )
    assert accepted.quality_state == "usable"


def test_cross_device_requires_materially_newer_plausible_observation() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)
    first_device = uuid.uuid4()
    second_device = uuid.uuid4()
    existing = ExistingLocation(
        source_device_id=first_device,
        latitude=40.0,
        longitude=-75.0,
        observed_at=now - timedelta(seconds=2),
        horizontal_accuracy_m=10,
        client_sequence=50,
    )

    with pytest.raises(LocationPolicyError) as conflict:
        evaluate_location_sample(
            sample(now - timedelta(seconds=2), client_sequence=1),
            source_device_id=second_device,
            policy=policy(),
            now=now,
            existing=existing,
        )
    assert conflict.value.code == "LOCATION_SAMPLE_CONFLICT"

    accepted = evaluate_location_sample(
        sample(now, latitude=40.0001, client_sequence=1),
        source_device_id=second_device,
        policy=policy(),
        now=now,
        existing=existing,
    )
    assert accepted.quality_state == "usable"


def test_implausible_movement_fails_without_distance_or_threshold_detail() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)
    device_id = uuid.uuid4()
    existing = ExistingLocation(
        source_device_id=device_id,
        latitude=40.0,
        longitude=-75.0,
        observed_at=now - timedelta(seconds=1),
        horizontal_accuracy_m=5,
        client_sequence=1,
    )

    with pytest.raises(LocationPolicyError) as raised:
        evaluate_location_sample(
            sample(now, latitude=41.0, longitude=-74.0, client_sequence=2),
            source_device_id=device_id,
            policy=policy(),
            now=now,
            existing=existing,
        )

    assert raised.value.code == "LOCATION_MOVEMENT_IMPLAUSIBLE"
    assert raised.value.detail == "The location movement is not plausible."


def test_settings_create_a_versioned_bounded_policy() -> None:
    settings = Settings(
        environment="test",
        location_policy_version="test-v2",
        location_max_usable_accuracy_m=75,
        location_max_retained_accuracy_m=500,
    )

    resolved = policy_from_settings(settings)

    assert resolved.version == "test-v2"
    assert resolved.max_usable_accuracy_m == 75
    assert resolved.max_retained_accuracy_m == 500


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "location_max_usable_accuracy_m": 501,
            "location_max_retained_accuracy_m": 500,
        },
        {
            "location_usable_ttl_seconds": 60,
            "location_degraded_ttl_seconds": 61,
        },
    ],
)
def test_inconsistent_location_policy_configuration_fails_closed(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        Settings(environment="test", **overrides)  # type: ignore[arg-type]
