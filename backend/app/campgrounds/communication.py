from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.campgrounds.context import CurrentCampgroundContext, derive_current_campground_context
from app.campgrounds.contracts import CampgroundCommunicationContext
from app.ptt.proximity import EligibleReceiveGrant


@dataclass(frozen=True, slots=True)
class CampgroundCommunicationComposition:
    context: CampgroundCommunicationContext
    eligible_receivers: tuple[EligibleReceiveGrant, ...]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def compose_campground_communication(
    *,
    sender_context: CurrentCampgroundContext | None,
    already_authorized_receivers: tuple[EligibleReceiveGrant, ...],
    receiver_contexts: Mapping[uuid.UUID, CurrentCampgroundContext | None],
    now: datetime,
) -> CampgroundCommunicationComposition | None:
    evaluated_at = _as_utc(now)
    if sender_context is None or _as_utc(sender_context.expires_at) <= evaluated_at:
        return None

    campground_id = sender_context.label.campground_id
    narrowed = tuple(
        receiver
        for receiver in already_authorized_receivers
        if (
            (current := receiver_contexts.get(receiver.account_id)) is not None
            and _as_utc(current.expires_at) > evaluated_at
            and current.label.campground_id == campground_id
        )
    )
    return CampgroundCommunicationComposition(
        context=CampgroundCommunicationContext(campground_id=campground_id),
        eligible_receivers=narrowed,
    )


async def compose_current_campground_communication(
    db: AsyncSession,
    *,
    sender_account_id: uuid.UUID,
    already_authorized_receivers: tuple[EligibleReceiveGrant, ...],
    location_policy_version: str,
    now: datetime | None = None,
) -> CampgroundCommunicationComposition | None:
    evaluated_at = _as_utc(now or datetime.now(UTC))
    sender_context = await derive_current_campground_context(
        db,
        account_id=sender_account_id,
        location_policy_version=location_policy_version,
        now=evaluated_at,
    )
    if sender_context is None:
        return None

    receiver_contexts: dict[uuid.UUID, CurrentCampgroundContext | None] = {}
    for receiver in already_authorized_receivers:
        if receiver.account_id in receiver_contexts:
            continue
        receiver_contexts[receiver.account_id] = await derive_current_campground_context(
            db,
            account_id=receiver.account_id,
            location_policy_version=location_policy_version,
            now=evaluated_at,
        )

    return compose_campground_communication(
        sender_context=sender_context,
        already_authorized_receivers=already_authorized_receivers,
        receiver_contexts=receiver_contexts,
        now=evaluated_at,
    )
