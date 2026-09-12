from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from geoalchemy2 import Geometry
from sqlalchemy import cast as sql_cast
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.campgrounds.contracts import CampgroundContextLabel
from app.campgrounds.models import Campground
from app.db.models import Account, CurrentLocation, LocationConsentEvent, Session

# Deterministic local/CI policy only. This is not a campground boundary or provider claim.
# It is intentionally internal and is never exposed as an occupancy/presence radius.
DETERMINISTIC_CONTEXT_DISTANCE_M = 2_500.0


@dataclass(frozen=True, slots=True)
class AuthorizedCurrentPoint:
    latitude: float
    longitude: float
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class CurrentCampgroundContext:
    label: CampgroundContextLabel
    expires_at: datetime


def _distance_m(*, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return deterministic great-circle distance without retaining either point."""

    radius_m = 6_371_008.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius_m * math.asin(math.sqrt(a))


def match_current_campground(
    point: AuthorizedCurrentPoint,
    campgrounds: list[Campground],
) -> CurrentCampgroundContext | None:
    """Narrow an already-authorized current point to one deterministic campground label."""

    candidates = [
        (
            _distance_m(
                lat1=point.latitude,
                lon1=point.longitude,
                lat2=campground.latitude,
                lon2=campground.longitude,
            ),
            campground,
        )
        for campground in campgrounds
    ]
    candidates = [item for item in candidates if item[0] <= DETERMINISTIC_CONTEXT_DISTANCE_M]
    if not candidates:
        return None

    _, campground = min(candidates, key=lambda item: (item[0], item[1].campground_id))
    return CurrentCampgroundContext(
        label=CampgroundContextLabel(
            campground_id=campground.campground_id,
            name=campground.name,
            state="current",
        ),
        expires_at=point.expires_at,
    )


async def _authorized_current_point(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    location_policy_version: str,
    now: datetime,
) -> AuthorizedCurrentPoint | None:
    consent = aliased(LocationConsentEvent)
    geometry = sql_cast(
        CurrentLocation.position,
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
    )
    active_source_session = exists(
        select(Session.id).where(
            Session.account_id == CurrentLocation.account_id,
            Session.device_id == CurrentLocation.source_device_id,
            Session.revoked_at.is_(None),
            Session.expires_at > now,
        )
    )
    latest_consent_id = (
        select(LocationConsentEvent.id)
        .where(LocationConsentEvent.account_id == CurrentLocation.account_id)
        .order_by(
            LocationConsentEvent.decided_at.desc(),
            LocationConsentEvent.created_at.desc(),
            LocationConsentEvent.id.desc(),
        )
        .limit(1)
        .correlate(CurrentLocation)
        .scalar_subquery()
    )
    row = (
        await db.execute(
            select(
                CurrentLocation.expires_at,
                geometry.ST_Y().label("latitude"),
                geometry.ST_X().label("longitude"),
            )
            .join(Account, Account.id == CurrentLocation.account_id)
            .join(consent, consent.id == latest_consent_id)
            .where(
                CurrentLocation.account_id == account_id,
                CurrentLocation.expires_at > now,
                CurrentLocation.quality_state == "usable",
                CurrentLocation.consent_policy_version == location_policy_version,
                Account.status == "active",
                consent.decision == "granted",
                consent.policy_version == location_policy_version,
                active_source_session,
            )
        )
    ).one_or_none()
    if row is None:
        return None
    return AuthorizedCurrentPoint(
        latitude=float(row.latitude),
        longitude=float(row.longitude),
        expires_at=row.expires_at,
    )


async def derive_current_campground_context(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    location_policy_version: str,
    now: datetime | None = None,
) -> CurrentCampgroundContext | None:
    """Derive ephemeral campground context from existing authorized current state only."""

    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    point = await _authorized_current_point(
        db,
        account_id=account_id,
        location_policy_version=location_policy_version,
        now=current_time,
    )
    if point is None:
        return None

    campgrounds = list(
        (
            await db.scalars(
                select(Campground)
                .where(
                    Campground.source == "deterministic_local",
                    Campground.freshness == "deterministic",
                )
                .order_by(Campground.campground_id)
            )
        ).all()
    )
    return match_current_campground(point, campgrounds)
