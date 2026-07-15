import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.config import Settings

EARTH_RADIUS_M = 6_371_008.8


class LocationPolicyError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class LocationPolicy:
    version: str
    max_sample_age_seconds: int
    max_future_seconds: int
    max_usable_accuracy_m: float
    max_retained_accuracy_m: float
    max_reported_speed_mps: float
    max_plausible_speed_mps: float
    plausibility_slack_m: float
    usable_ttl_seconds: int
    degraded_ttl_seconds: int
    cross_device_newer_seconds: int


@dataclass(frozen=True)
class LocationSample:
    latitude: float
    longitude: float
    observed_at: datetime
    horizontal_accuracy_m: float
    heading_deg: float | None
    speed_mps: float | None
    client_sequence: int
    consent_policy_version: str


@dataclass(frozen=True)
class ExistingLocation:
    source_device_id: uuid.UUID
    latitude: float
    longitude: float
    observed_at: datetime
    horizontal_accuracy_m: float
    client_sequence: int


@dataclass(frozen=True)
class LocationDecision:
    quality_state: str
    expires_at: datetime


def policy_from_settings(settings: Settings) -> LocationPolicy:
    return LocationPolicy(
        version=settings.location_policy_version,
        max_sample_age_seconds=settings.location_max_sample_age_seconds,
        max_future_seconds=settings.location_max_future_seconds,
        max_usable_accuracy_m=settings.location_max_usable_accuracy_m,
        max_retained_accuracy_m=settings.location_max_retained_accuracy_m,
        max_reported_speed_mps=settings.location_max_reported_speed_mps,
        max_plausible_speed_mps=settings.location_max_plausible_speed_mps,
        plausibility_slack_m=settings.location_plausibility_slack_m,
        usable_ttl_seconds=settings.location_usable_ttl_seconds,
        degraded_ttl_seconds=settings.location_degraded_ttl_seconds,
        cross_device_newer_seconds=settings.location_cross_device_newer_seconds,
    )


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise LocationPolicyError(
            "LOCATION_TIME_INVALID",
            "The location observation time is invalid.",
        )
    return value.astimezone(UTC)


def _finite(value: float) -> bool:
    return math.isfinite(value)


def _validate_sample_shape(sample: LocationSample, policy: LocationPolicy) -> None:
    if (
        not _finite(sample.latitude)
        or not _finite(sample.longitude)
        or not -90 <= sample.latitude <= 90
        or not -180 <= sample.longitude <= 180
    ):
        raise LocationPolicyError(
            "LOCATION_COORDINATES_INVALID",
            "The location coordinates are invalid.",
        )
    if (
        not _finite(sample.horizontal_accuracy_m)
        or sample.horizontal_accuracy_m < 0
        or sample.horizontal_accuracy_m > policy.max_retained_accuracy_m
    ):
        raise LocationPolicyError(
            "LOCATION_ACCURACY_UNUSABLE",
            "The location accuracy is not usable.",
        )
    if sample.heading_deg is not None and (
        not _finite(sample.heading_deg) or not 0 <= sample.heading_deg < 360
    ):
        raise LocationPolicyError(
            "LOCATION_HEADING_INVALID",
            "The location heading is invalid.",
        )
    if sample.speed_mps is not None and (
        not _finite(sample.speed_mps)
        or sample.speed_mps < 0
        or sample.speed_mps > policy.max_reported_speed_mps
    ):
        raise LocationPolicyError(
            "LOCATION_SPEED_INVALID",
            "The location speed is invalid.",
        )
    if sample.client_sequence < 1:
        raise LocationPolicyError(
            "LOCATION_SEQUENCE_INVALID",
            "The location sequence is invalid.",
        )
    if sample.consent_policy_version != policy.version:
        raise LocationPolicyError(
            "LOCATION_POLICY_MISMATCH",
            "The foreground-location policy must be accepted again.",
        )


def _validate_time(sample: LocationSample, *, now: datetime, policy: LocationPolicy) -> datetime:
    observed_at = _aware_utc(sample.observed_at)
    if observed_at > now + timedelta(seconds=policy.max_future_seconds):
        raise LocationPolicyError(
            "LOCATION_TIME_INVALID",
            "The location observation time is invalid.",
        )
    if observed_at < now - timedelta(seconds=policy.max_sample_age_seconds):
        raise LocationPolicyError(
            "LOCATION_SAMPLE_STALE",
            "The location sample is stale.",
        )
    return observed_at


def _distance_m(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    first_latitude_rad = math.radians(first_latitude)
    second_latitude_rad = math.radians(second_latitude)
    latitude_delta = second_latitude_rad - first_latitude_rad
    longitude_delta = math.radians(second_longitude - first_longitude)
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(first_latitude_rad)
        * math.cos(second_latitude_rad)
        * math.sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(haversine)))


def _validate_replacement(
    sample: LocationSample,
    *,
    observed_at: datetime,
    source_device_id: uuid.UUID,
    existing: ExistingLocation,
    policy: LocationPolicy,
) -> None:
    existing_observed_at = _aware_utc(existing.observed_at)
    same_device = existing.source_device_id == source_device_id
    if same_device:
        if (
            sample.client_sequence <= existing.client_sequence
            or observed_at <= existing_observed_at
        ):
            raise LocationPolicyError(
                "LOCATION_SAMPLE_OUT_OF_ORDER",
                "The location sample is not newer than the current sample.",
            )
    elif observed_at < existing_observed_at + timedelta(seconds=policy.cross_device_newer_seconds):
        raise LocationPolicyError(
            "LOCATION_SAMPLE_CONFLICT",
            "A newer location sample is already current.",
        )

    elapsed_seconds = (observed_at - existing_observed_at).total_seconds()
    if elapsed_seconds <= 0:
        raise LocationPolicyError(
            "LOCATION_SAMPLE_CONFLICT",
            "A newer location sample is already current.",
        )
    distance_m = _distance_m(
        existing.latitude,
        existing.longitude,
        sample.latitude,
        sample.longitude,
    )
    tolerated_distance_m = (
        policy.max_plausible_speed_mps * elapsed_seconds
        + policy.plausibility_slack_m
        + existing.horizontal_accuracy_m
        + sample.horizontal_accuracy_m
    )
    if distance_m > tolerated_distance_m:
        raise LocationPolicyError(
            "LOCATION_MOVEMENT_IMPLAUSIBLE",
            "The location movement is not plausible.",
        )


def evaluate_location_sample(
    sample: LocationSample,
    *,
    source_device_id: uuid.UUID,
    policy: LocationPolicy,
    now: datetime,
    existing: ExistingLocation | None = None,
) -> LocationDecision:
    received_at = _aware_utc(now)
    _validate_sample_shape(sample, policy)
    observed_at = _validate_time(sample, now=received_at, policy=policy)
    if existing is not None:
        _validate_replacement(
            sample,
            observed_at=observed_at,
            source_device_id=source_device_id,
            existing=existing,
            policy=policy,
        )

    usable = sample.horizontal_accuracy_m <= policy.max_usable_accuracy_m
    ttl_seconds = policy.usable_ttl_seconds if usable else policy.degraded_ttl_seconds
    return LocationDecision(
        quality_state="usable" if usable else "degraded",
        expires_at=received_at + timedelta(seconds=ttl_seconds),
    )
