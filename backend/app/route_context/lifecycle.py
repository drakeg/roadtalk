from __future__ import annotations

import hashlib
import hmac
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from geoalchemy2 import Geometry
from sqlalchemy import cast as sql_cast
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import AccountRouteMode, CurrentLocation
from app.route_context.models import CurrentRouteContext
from app.route_context.provider import (
    RouteContextConfidence,
    RouteContextMatchRequest,
    RouteContextMatcher,
    RouteContextProvider,
    RouteContextProviderUnavailable,
)


@dataclass(frozen=True, slots=True)
class RouteContextReceipt:
    available: bool
    source_location_version: int | None
    expires_at: datetime | None
    version: int | None


def corridor_digest(*, secret: str, provider_version: str, provider_corridor_ref: str) -> str:
    message = (f"roadtalk-route-corridor-v1\0{provider_version}\0{provider_corridor_ref}").encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


async def _delete_context(db: AsyncSession, *, account_id: uuid.UUID) -> bool:
    deleted = await db.scalar(
        delete(CurrentRouteContext)
        .where(CurrentRouteContext.account_id == account_id)
        .returning(CurrentRouteContext.account_id)
    )
    return deleted is not None


async def refresh_current_route_context(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    provider: RouteContextProvider,
    settings: Settings,
    now: datetime | None = None,
) -> RouteContextReceipt:
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
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

    mode = await db.scalar(
        select(AccountRouteMode.mode).where(AccountRouteMode.account_id == account_id)
    )
    if row is None or mode != "same_road":
        await _delete_context(db, account_id=account_id)
        await db.commit()
        return RouteContextReceipt(False, None, None, None)

    location = cast(CurrentLocation, row[0])
    if (
        location.quality_state != "usable"
        or location.expires_at <= current_time
        or location.horizontal_accuracy_m > settings.location_max_usable_accuracy_m
    ):
        await _delete_context(db, account_id=account_id)
        await db.commit()
        return RouteContextReceipt(False, location.version, None, None)

    request = RouteContextMatchRequest(
        latitude=float(row.latitude),
        longitude=float(row.longitude),
        horizontal_accuracy_m=location.horizontal_accuracy_m,
        heading_degrees=location.heading_deg,
        speed_mps=location.speed_mps,
        observed_at=location.observed_at,
        source_location_version=location.version,
    )
    matcher = RouteContextMatcher(
        provider,
        timeout_ms=settings.route_context_timeout_ms,
        max_ttl_seconds=settings.route_context_ttl_seconds,
        expected_policy_version=settings.route_context_policy_version,
        clock=lambda: current_time,
    )
    try:
        result = await matcher.match(request)
    except RouteContextProviderUnavailable:
        await _delete_context(db, account_id=account_id)
        await db.commit()
        return RouteContextReceipt(False, location.version, None, None)

    if result.confidence is not RouteContextConfidence.CONFIDENT:
        await _delete_context(db, account_id=account_id)
        await db.commit()
        return RouteContextReceipt(False, location.version, None, None)
    if result.expires_at > location.expires_at:
        await _delete_context(db, account_id=account_id)
        await db.commit()
        return RouteContextReceipt(False, location.version, None, None)

    digest = corridor_digest(
        secret=settings.token_signing_key.get_secret_value(),
        provider_version=result.provider_version,
        provider_corridor_ref=result.provider_corridor_ref,
    )
    current = await db.scalar(
        select(CurrentRouteContext)
        .where(CurrentRouteContext.account_id == account_id)
        .with_for_update()
    )
    if current is not None and current.source_location_version > result.source_location_version:
        await db.commit()
        return RouteContextReceipt(False, location.version, None, None)
    if current is not None and current.source_location_version == result.source_location_version:
        if (
            current.corridor_digest == digest
            and current.direction == result.direction.value
            and current.provider_version == result.provider_version
            and current.policy_version == result.policy_version
            and current.expires_at == result.expires_at
        ):
            await db.commit()
            return RouteContextReceipt(
                True,
                current.source_location_version,
                current.expires_at,
                current.version,
            )
        await _delete_context(db, account_id=account_id)
        await db.commit()
        return RouteContextReceipt(False, location.version, None, None)

    if current is None:
        current = CurrentRouteContext(
            account_id=account_id,
            corridor_digest=digest,
            direction=result.direction.value,
            confidence=result.confidence.value,
            source_location_version=result.source_location_version,
            provider_version=result.provider_version,
            policy_version=result.policy_version,
            matched_at=result.matched_at,
            expires_at=result.expires_at,
            version=1,
        )
        db.add(current)
    else:
        current.corridor_digest = digest
        current.direction = result.direction.value
        current.confidence = result.confidence.value
        current.source_location_version = result.source_location_version
        current.provider_version = result.provider_version
        current.policy_version = result.policy_version
        current.matched_at = result.matched_at
        current.expires_at = result.expires_at
        current.version += 1

    await db.commit()
    return RouteContextReceipt(
        True,
        current.source_location_version,
        current.expires_at,
        current.version,
    )


async def delete_expired_route_contexts(
    db: AsyncSession,
    *,
    now: datetime | None = None,
) -> int:
    cutoff = (now or datetime.now(UTC)).astimezone(UTC)
    deleted = await db.scalars(
        delete(CurrentRouteContext)
        .where(CurrentRouteContext.expires_at <= cutoff)
        .returning(CurrentRouteContext.account_id)
    )
    await db.commit()
    return len(deleted.all())
