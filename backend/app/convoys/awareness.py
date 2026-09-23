from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.convoys.contracts import ConvoyAwarenessMember, ConvoyAwarenessSnapshot
from app.db.models import (
    Account,
    Convoy,
    ConvoyMembership,
    CurrentLocation,
    LocationConsentEvent,
    Profile,
    Session,
)


async def current_convoy_awareness(
    db: AsyncSession,
    *,
    viewer_account_id: uuid.UUID,
    location_policy_version: str,
    now: datetime | None = None,
) -> ConvoyAwarenessSnapshot | None:
    """Derive member-only convoy awareness from authoritative current state."""

    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    viewer_membership = await db.scalar(
        select(ConvoyMembership)
        .join(Convoy, Convoy.id == ConvoyMembership.convoy_id)
        .where(
            ConvoyMembership.account_id == viewer_account_id,
            ConvoyMembership.state == "active",
            or_(
                ConvoyMembership.expires_at.is_(None),
                ConvoyMembership.expires_at > current_time,
            ),
            Convoy.state == "active",
        )
    )
    if viewer_membership is None:
        return None

    consent = aliased(LocationConsentEvent)
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
    active_source_session = exists(
        select(Session.id).where(
            Session.account_id == CurrentLocation.account_id,
            Session.device_id == CurrentLocation.source_device_id,
            Session.revoked_at.is_(None),
            Session.expires_at > current_time,
        )
    )

    rows = (
        await db.execute(
            select(
                ConvoyMembership.account_id,
                Profile.display_callsign,
                ConvoyMembership.role,
                CurrentLocation.expires_at,
            )
            .join(Account, Account.id == ConvoyMembership.account_id)
            .join(Profile, Profile.account_id == ConvoyMembership.account_id)
            .join(
                CurrentLocation,
                CurrentLocation.account_id == ConvoyMembership.account_id,
            )
            .join(consent, consent.id == latest_consent_id)
            .where(
                ConvoyMembership.convoy_id == viewer_membership.convoy_id,
                ConvoyMembership.state == "active",
                or_(
                    ConvoyMembership.expires_at.is_(None),
                    ConvoyMembership.expires_at > current_time,
                ),
                Account.status == "active",
                Profile.display_callsign.is_not(None),
                CurrentLocation.expires_at > current_time,
                CurrentLocation.quality_state == "usable",
                CurrentLocation.consent_policy_version == location_policy_version,
                consent.decision == "granted",
                consent.policy_version == location_policy_version,
                active_source_session,
            )
            .order_by(ConvoyMembership.role, Profile.normalized_callsign)
        )
    ).all()

    members = tuple(
        ConvoyAwarenessMember(
            account_id=row.account_id,
            callsign=cast(str, row.display_callsign),
            role=row.role,
            expires_at=row.expires_at,
        )
        for row in rows
    )
    if not members:
        return ConvoyAwarenessSnapshot(
            convoy_id=viewer_membership.convoy_id,
            expires_at=current_time,
            members=(),
        )
    return ConvoyAwarenessSnapshot(
        convoy_id=viewer_membership.convoy_id,
        expires_at=min(member.expires_at for member in members),
        members=members,
    )
