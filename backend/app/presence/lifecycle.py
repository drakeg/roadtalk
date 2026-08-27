from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from geoalchemy2 import Geometry
from sqlalchemy import and_, cast as sql_cast, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.db.models import Account, CurrentLocation, LocationConsentEvent, Session
from app.presence.policy import PresenceCell, PresencePoint, aggregate_presence

PRESENCE_POLICY_VERSION = "presence-v1"


@dataclass(frozen=True, slots=True)
class PresenceSnapshot:
    expires_at: datetime
    cells: tuple[PresenceCell, ...]


async def current_presence_snapshot(
    db: AsyncSession,
    *,
    viewer_account_id: uuid.UUID,
    location_policy_version: str,
    now: datetime | None = None,
) -> PresenceSnapshot:
    """Derive presence from current eligible location; never persist a presence history."""

    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    consent = aliased(LocationConsentEvent)
    newer_consent = aliased(LocationConsentEvent)
    geometry = sql_cast(
        CurrentLocation.position,
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
    )
    active_source_session = exists(
        select(Session.id).where(
            Session.account_id == CurrentLocation.account_id,
            Session.device_id == CurrentLocation.source_device_id,
            Session.revoked_at.is_(None),
            Session.expires_at > current_time,
        )
    )
    no_newer_consent = ~exists(
        select(newer_consent.id).where(
            newer_consent.account_id == consent.account_id,
            newer_consent.decided_at > consent.decided_at,
        )
    )

    rows = await db.execute(
        select(
            CurrentLocation.account_id,
            CurrentLocation.expires_at,
            func.ST_Y(geometry).label("latitude"),
            func.ST_X(geometry).label("longitude"),
        )
        .join(Account, Account.id == CurrentLocation.account_id)
        .join(consent, consent.account_id == CurrentLocation.account_id)
        .where(
            CurrentLocation.account_id != viewer_account_id,
            CurrentLocation.expires_at > current_time,
            CurrentLocation.quality_state == "usable",
            CurrentLocation.consent_policy_version == location_policy_version,
            Account.status == "active",
            consent.decision == "granted",
            consent.policy_version == location_policy_version,
            no_newer_consent,
            active_source_session,
        )
    )

    points: list[PresencePoint] = []
    expiries: list[datetime] = []
    for row in rows:
        points.append(
            PresencePoint(
                account_key=str(row.account_id),
                latitude=float(row.latitude),
                longitude=float(row.longitude),
            )
        )
        expiries.append(row.expires_at)

    cells = aggregate_presence(points)
    if not cells:
        return PresenceSnapshot(expires_at=current_time, cells=())
    return PresenceSnapshot(expires_at=min(expiries), cells=cells)
