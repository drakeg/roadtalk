import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement

from app.db.models import CurrentLocation, LocationConsentEvent


class NearbySummaryError(ValueError):
    code = "LOCATION_UNAVAILABLE"
    detail = "A fresh usable location is required."


@dataclass(frozen=True)
class NearbySummary:
    availability: Literal["available"]
    bucket: Literal["none", "few", "many"]
    freshness: Literal["fresh"]
    expires_at: datetime


def nearby_bucket(count: int, *, many_threshold: int) -> Literal["none", "few", "many"]:
    if count == 0:
        return "none"
    if count < many_threshold:
        return "few"
    return "many"


def _active_consent_for_location(*, policy_version: str) -> ColumnElement[bool]:
    latest = aliased(LocationConsentEvent)
    latest_id = (
        select(latest.id)
        .where(latest.account_id == CurrentLocation.account_id)
        .order_by(latest.decided_at.desc(), latest.created_at.desc(), latest.id.desc())
        .limit(1)
        .correlate(CurrentLocation)
        .scalar_subquery()
    )
    return (
        select(LocationConsentEvent.id)
        .where(
            LocationConsentEvent.id == latest_id,
            LocationConsentEvent.decision == "granted",
            LocationConsentEvent.policy_version == policy_version,
        )
        .exists()
    )


async def get_nearby_summary(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    policy_version: str,
    max_usable_accuracy_m: float,
    radius_m: float,
    many_threshold: int,
    now: datetime | None = None,
) -> NearbySummary:
    cutoff = (now or datetime.now(UTC)).astimezone(UTC)
    active_consent = _active_consent_for_location(policy_version=policy_version)
    caller = await db.scalar(
        select(CurrentLocation).where(
            CurrentLocation.account_id == account_id,
            CurrentLocation.quality_state == "usable",
            CurrentLocation.expires_at > cutoff,
            CurrentLocation.horizontal_accuracy_m <= max_usable_accuracy_m,
            CurrentLocation.consent_policy_version == policy_version,
            active_consent,
        )
    )
    if caller is None:
        raise NearbySummaryError

    count = await db.scalar(
        select(func.count())
        .select_from(CurrentLocation)
        .where(
            CurrentLocation.account_id != account_id,
            CurrentLocation.quality_state == "usable",
            CurrentLocation.expires_at > cutoff,
            CurrentLocation.horizontal_accuracy_m <= max_usable_accuracy_m,
            CurrentLocation.consent_policy_version == policy_version,
            active_consent,
            func.ST_DWithin(CurrentLocation.position, caller.position, radius_m),
        )
    )
    return NearbySummary(
        availability="available",
        bucket=nearby_bucket(int(count or 0), many_threshold=many_threshold),
        freshness="fresh",
        expires_at=caller.expires_at,
    )
