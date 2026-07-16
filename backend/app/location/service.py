import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from geoalchemy2 import Geometry, WKTElement
from geoalchemy2.elements import WKBElement
from sqlalchemy import cast as sql_cast
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CurrentLocation, Device, LocationConsentEvent
from app.location.quality import (
    ExistingLocation,
    LocationPolicy,
    LocationPolicyError,
    LocationSample,
    evaluate_location_sample,
)


@dataclass(frozen=True)
class LocationReceipt:
    accepted_sequence: int
    quality_state: str
    expires_at: datetime
    policy_version: str
    version: int


async def _require_source_ownership(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
) -> None:
    owner = await db.scalar(select(Device.account_id).where(Device.id == device_id))
    if owner != account_id:
        raise LocationPolicyError(
            "LOCATION_SOURCE_INVALID",
            "The location source is invalid.",
        )


async def _require_current_consent(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    policy_version: str,
) -> None:
    current = (
        await db.scalars(
            select(LocationConsentEvent)
            .where(LocationConsentEvent.account_id == account_id)
            .order_by(LocationConsentEvent.decided_at.desc(), LocationConsentEvent.id.desc())
            .limit(1)
        )
    ).first()
    if current is None or current.decision != "granted" or current.policy_version != policy_version:
        raise LocationPolicyError(
            "LOCATION_CONSENT_REQUIRED",
            "Foreground-location consent is required.",
        )


async def _locked_current_location(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
) -> tuple[CurrentLocation, float, float] | None:
    geometry = sql_cast(
        CurrentLocation.position,
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
    )
    row = (
        await db.execute(
            select(
                CurrentLocation,
                func.ST_Y(geometry).label("latitude"),
                func.ST_X(geometry).label("longitude"),
            )
            .where(CurrentLocation.account_id == account_id)
            .with_for_update(of=CurrentLocation)
        )
    ).one_or_none()
    if row is None:
        return None
    return row[0], float(row.latitude), float(row.longitude)


async def record_current_location(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    sample: LocationSample,
    policy: LocationPolicy,
    now: datetime | None = None,
) -> LocationReceipt:
    received_at = (now or datetime.now(UTC)).astimezone(UTC)
    await _require_source_ownership(
        db,
        account_id=account_id,
        device_id=device_id,
    )
    await _require_current_consent(
        db,
        account_id=account_id,
        policy_version=sample.consent_policy_version,
    )
    locked = await _locked_current_location(db, account_id=account_id)
    existing: ExistingLocation | None = None
    current: CurrentLocation | None = None
    if locked is not None:
        current, latitude, longitude = locked
        existing = ExistingLocation(
            source_device_id=current.source_device_id,
            latitude=latitude,
            longitude=longitude,
            observed_at=current.observed_at,
            horizontal_accuracy_m=current.horizontal_accuracy_m,
            client_sequence=current.client_sequence,
        )

    decision = evaluate_location_sample(
        sample,
        source_device_id=device_id,
        policy=policy,
        now=received_at,
        existing=existing,
    )
    position = cast(
        WKBElement,
        WKTElement(f"POINT({sample.longitude} {sample.latitude})", srid=4326),
    )
    if current is None:
        current = CurrentLocation(
            account_id=account_id,
            source_device_id=device_id,
            position=position,
            observed_at=sample.observed_at.astimezone(UTC),
            received_at=received_at,
            horizontal_accuracy_m=sample.horizontal_accuracy_m,
            heading_deg=sample.heading_deg,
            speed_mps=sample.speed_mps,
            client_sequence=sample.client_sequence,
            expires_at=decision.expires_at,
            consent_policy_version=policy.version,
            quality_state=decision.quality_state,
            version=1,
        )
        db.add(current)
    else:
        current.source_device_id = device_id
        current.position = position
        current.observed_at = sample.observed_at.astimezone(UTC)
        current.received_at = received_at
        current.horizontal_accuracy_m = sample.horizontal_accuracy_m
        current.heading_deg = sample.heading_deg
        current.speed_mps = sample.speed_mps
        current.client_sequence = sample.client_sequence
        current.expires_at = decision.expires_at
        current.consent_policy_version = policy.version
        current.quality_state = decision.quality_state
        current.version += 1

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise LocationPolicyError(
            "LOCATION_SAMPLE_CONFLICT",
            "A newer location sample is already current.",
        ) from exc

    return LocationReceipt(
        accepted_sequence=current.client_sequence,
        quality_state=current.quality_state,
        expires_at=current.expires_at,
        policy_version=current.consent_policy_version,
        version=current.version,
    )


async def delete_expired_locations(db: AsyncSession, *, now: datetime | None = None) -> int:
    cutoff = (now or datetime.now(UTC)).astimezone(UTC)
    deleted_ids = await db.scalars(
        delete(CurrentLocation)
        .where(CurrentLocation.expires_at <= cutoff)
        .returning(CurrentLocation.account_id)
    )
    await db.commit()
    return len(deleted_ids.all())


async def delete_current_location(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
) -> bool:
    deleted_id = await db.scalar(
        delete(CurrentLocation)
        .where(CurrentLocation.account_id == account_id)
        .returning(CurrentLocation.account_id)
    )
    await db.commit()
    return deleted_id is not None
