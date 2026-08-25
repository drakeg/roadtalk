import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from geoalchemy2.elements import WKBElement
from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement

from app.config import Settings
from app.db.models import (
    Account,
    AccountRouteMode,
    Channel,
    ChannelMembership,
    ChannelSelection,
    CurrentLocation,
    Device,
    LocationConsentEvent,
    MediaGrant,
    Session,
)
from app.route_context.models import CurrentRouteContext


class ProximityEligibilityError(ValueError):
    code = "PTT_LOCATION_UNAVAILABLE"
    detail = "A current usable location is required."


@dataclass(frozen=True)
class ProximityPolicy:
    version: str
    radius_m: float
    delivery_window_seconds: int
    location_policy_version: str
    ptt_policy_version: str
    max_usable_accuracy_m: float
    room_ref: str
    channel_id: uuid.UUID


@dataclass(frozen=True)
class EligibleReceiveGrant:
    receive_grant_id: uuid.UUID
    account_id: uuid.UUID
    device_id: uuid.UUID
    participant_ref: str


_TRAVEL_DIRECTIONS = (
    "north",
    "northeast",
    "east",
    "southeast",
    "south",
    "southwest",
    "west",
    "northwest",
)


def directions_compatible(left: str, right: str) -> bool:
    """Return deterministic coarse direction compatibility with circular wraparound."""
    if left not in _TRAVEL_DIRECTIONS or right not in _TRAVEL_DIRECTIONS:
        return False
    left_index = _TRAVEL_DIRECTIONS.index(left)
    right_index = _TRAVEL_DIRECTIONS.index(right)
    distance = abs(left_index - right_index)
    circular_distance = min(distance, len(_TRAVEL_DIRECTIONS) - distance)
    return circular_distance <= 1


def proximity_policy_from_settings(
    settings: Settings,
    *,
    channel_id: uuid.UUID | None = None,
    room_ref: str | None = None,
) -> ProximityPolicy:
    from app.channels.constants import GENERAL_CHANNEL_ID

    return ProximityPolicy(
        version=settings.ptt_proximity_policy_version,
        radius_m=settings.ptt_proximity_radius_m,
        delivery_window_seconds=settings.ptt_transmit_grant_ttl_seconds,
        location_policy_version=settings.location_policy_version,
        ptt_policy_version=settings.ptt_policy_version,
        max_usable_accuracy_m=settings.location_max_usable_accuracy_m,
        room_ref=room_ref or settings.ptt_controlled_room_ref,
        channel_id=channel_id or GENERAL_CHANNEL_ID,
    )


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


def _active_session_through(delivery_expires_at: datetime) -> ColumnElement[bool]:
    session_expires_at = delivery_expires_at.astimezone(UTC).replace(tzinfo=None)
    return exists(
        select(Session.id).where(
            Session.account_id == MediaGrant.account_id,
            Session.device_id == MediaGrant.device_id,
            Session.revoked_at.is_(None),
            Session.expires_at >= session_expires_at,
        )
    )


def eligible_receive_grants_statement(
    *,
    sender_account_id: uuid.UUID,
    sender_position: WKBElement,
    delivery_expires_at: datetime,
    policy: ProximityPolicy,
) -> Select[tuple[uuid.UUID, uuid.UUID, uuid.UUID, str]]:
    active_consent = _active_consent_for_location(policy_version=policy.location_policy_version)
    active_private_membership = exists(
        select(ChannelMembership.account_id).where(
            ChannelMembership.account_id == MediaGrant.account_id,
            ChannelMembership.channel_id == MediaGrant.channel_id,
            ChannelMembership.state == "active",
        )
    )
    return (
        select(
            MediaGrant.id,
            MediaGrant.account_id,
            MediaGrant.device_id,
            MediaGrant.provider_participant_ref,
        )
        .join(Account, Account.id == MediaGrant.account_id)
        .join(
            ChannelSelection,
            (ChannelSelection.account_id == MediaGrant.account_id)
            & (ChannelSelection.channel_id == MediaGrant.channel_id),
        )
        .join(Channel, Channel.id == MediaGrant.channel_id)
        .join(
            Device,
            (Device.id == MediaGrant.device_id) & (Device.account_id == MediaGrant.account_id),
        )
        .join(
            CurrentLocation,
            (CurrentLocation.account_id == MediaGrant.account_id)
            & (CurrentLocation.source_device_id == MediaGrant.device_id),
        )
        .where(
            MediaGrant.account_id != sender_account_id,
            MediaGrant.grant_kind == "receive",
            MediaGrant.action_scope == "subscribe",
            MediaGrant.policy_version == policy.ptt_policy_version,
            MediaGrant.channel_id == policy.channel_id,
            MediaGrant.provider_room_ref == policy.room_ref,
            MediaGrant.revoked_at.is_(None),
            MediaGrant.expires_at >= delivery_expires_at,
            Account.status == "active",
            Channel.enabled.is_(True),
            Channel.closed_at.is_(None),
            Channel.provider_room_ref == policy.room_ref,
            or_(Channel.channel_type == "public", active_private_membership),
            CurrentLocation.quality_state == "usable",
            CurrentLocation.expires_at >= delivery_expires_at,
            CurrentLocation.horizontal_accuracy_m <= policy.max_usable_accuracy_m,
            CurrentLocation.consent_policy_version == policy.location_policy_version,
            active_consent,
            _active_session_through(delivery_expires_at),
            func.ST_DWithin(CurrentLocation.position, sender_position, policy.radius_m),
        )
        .order_by(MediaGrant.id)
    )


async def _route_modes(
    db: AsyncSession,
    account_ids: set[uuid.UUID],
) -> dict[uuid.UUID, str]:
    rows = await db.execute(
        select(AccountRouteMode.account_id, AccountRouteMode.mode).where(
            AccountRouteMode.account_id.in_(account_ids)
        )
    )
    return {account_id: mode for account_id, mode in rows.all()}


async def _fresh_route_contexts(
    db: AsyncSession,
    account_ids: set[uuid.UUID],
    *,
    now: datetime,
) -> dict[uuid.UUID, CurrentRouteContext]:
    contexts = await db.scalars(
        select(CurrentRouteContext)
        .join(CurrentLocation, CurrentLocation.account_id == CurrentRouteContext.account_id)
        .where(
            CurrentRouteContext.account_id.in_(account_ids),
            CurrentRouteContext.expires_at > now,
            CurrentRouteContext.confidence == "confident",
            CurrentRouteContext.source_location_version == CurrentLocation.version,
        )
    )
    return {context.account_id: context for context in contexts.all()}


async def filter_same_road_receive_grants(
    db: AsyncSession,
    *,
    sender_account_id: uuid.UUID,
    eligible_receivers: tuple[EligibleReceiveGrant, ...],
    now: datetime,
) -> tuple[EligibleReceiveGrant, ...]:
    """Restrict an already-authorized nearby candidate set; never add recipients."""
    if not eligible_receivers:
        return ()

    receiver_account_ids = {receiver.account_id for receiver in eligible_receivers}
    account_ids = {sender_account_id, *receiver_account_ids}
    modes = await _route_modes(db, account_ids)
    sender_mode = modes.get(sender_account_id, "nearby")
    same_road_receivers = {
        account_id
        for account_id in receiver_account_ids
        if modes.get(account_id, "nearby") == "same_road"
    }
    if sender_mode != "same_road" and not same_road_receivers:
        return eligible_receivers

    context_ids = set(same_road_receivers)
    context_ids.add(sender_account_id)
    if sender_mode == "same_road":
        context_ids.update(receiver_account_ids)
    contexts = await _fresh_route_contexts(db, context_ids, now=now)
    sender_context = contexts.get(sender_account_id)

    filtered: list[EligibleReceiveGrant] = []
    for receiver in eligible_receivers:
        receiver_mode = modes.get(receiver.account_id, "nearby")
        if sender_mode != "same_road" and receiver_mode != "same_road":
            filtered.append(receiver)
            continue

        receiver_context = contexts.get(receiver.account_id)
        if sender_context is None or receiver_context is None:
            continue
        if sender_context.corridor_digest != receiver_context.corridor_digest:
            continue
        if not directions_compatible(sender_context.direction, receiver_context.direction):
            continue
        filtered.append(receiver)

    return tuple(filtered)


async def find_eligible_receive_grants(
    db: AsyncSession,
    *,
    sender_account_id: uuid.UUID,
    sender_device_id: uuid.UUID,
    policy: ProximityPolicy,
    now: datetime | None = None,
) -> tuple[EligibleReceiveGrant, ...]:
    evaluated_at = (now or datetime.now(UTC)).astimezone(UTC)
    delivery_expires_at = evaluated_at + timedelta(seconds=policy.delivery_window_seconds)
    active_consent = _active_consent_for_location(policy_version=policy.location_policy_version)
    active_private_membership = exists(
        select(ChannelMembership.account_id).where(
            ChannelMembership.account_id == sender_account_id,
            ChannelMembership.channel_id == policy.channel_id,
            ChannelMembership.state == "active",
        )
    )
    sender = await db.scalar(
        select(CurrentLocation)
        .join(ChannelSelection, ChannelSelection.account_id == CurrentLocation.account_id)
        .join(Channel, Channel.id == ChannelSelection.channel_id)
        .where(
            CurrentLocation.account_id == sender_account_id,
            CurrentLocation.source_device_id == sender_device_id,
            CurrentLocation.quality_state == "usable",
            CurrentLocation.expires_at >= delivery_expires_at,
            CurrentLocation.horizontal_accuracy_m <= policy.max_usable_accuracy_m,
            CurrentLocation.consent_policy_version == policy.location_policy_version,
            ChannelSelection.channel_id == policy.channel_id,
            Channel.enabled.is_(True),
            Channel.closed_at.is_(None),
            Channel.provider_room_ref == policy.room_ref,
            or_(Channel.channel_type == "public", active_private_membership),
            active_consent,
        )
    )
    if sender is None:
        raise ProximityEligibilityError

    result = await db.execute(
        eligible_receive_grants_statement(
            sender_account_id=sender_account_id,
            sender_position=sender.position,
            delivery_expires_at=delivery_expires_at,
            policy=policy,
        )
    )
    eligible = tuple(
        EligibleReceiveGrant(
            receive_grant_id=receive_grant_id,
            account_id=account_id,
            device_id=device_id,
            participant_ref=participant_ref,
        )
        for receive_grant_id, account_id, device_id, participant_ref in result.all()
    )
    return await filter_same_road_receive_grants(
        db,
        sender_account_id=sender_account_id,
        eligible_receivers=eligible,
        now=evaluated_at,
    )
