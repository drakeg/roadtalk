import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccountRouteMode, CurrentLocation
from app.ptt.proximity import EligibleReceiveGrant, ProximityPolicy, find_eligible_receive_grants
from app.route_context.models import CurrentRouteContext

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
    """Return deterministic coarse travel compatibility without exposing headings."""
    if left not in _TRAVEL_DIRECTIONS or right not in _TRAVEL_DIRECTIONS:
        return False
    left_index = _TRAVEL_DIRECTIONS.index(left)
    right_index = _TRAVEL_DIRECTIONS.index(right)
    distance = abs(left_index - right_index)
    circular_distance = min(distance, len(_TRAVEL_DIRECTIONS) - distance)
    return circular_distance <= 1


async def _route_modes(
    db: AsyncSession,
    account_ids: set[uuid.UUID],
) -> dict[uuid.UUID, str]:
    if not account_ids:
        return {}
    rows = await db.execute(
        select(AccountRouteMode.account_id, AccountRouteMode.mode).where(
            AccountRouteMode.account_id.in_(account_ids)
        )
    )
    return {account_id: mode for account_id, mode in rows.all()}


async def _fresh_contexts(
    db: AsyncSession,
    account_ids: set[uuid.UUID],
    *,
    now: datetime,
) -> dict[uuid.UUID, CurrentRouteContext]:
    if not account_ids:
        return {}
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
    now: datetime | None = None,
) -> tuple[EligibleReceiveGrant, ...]:
    """Apply Same-road only after prior proximity/channel/session/grant authorization."""
    if not eligible_receivers:
        return ()

    evaluated_at = (now or datetime.now(UTC)).astimezone(UTC)
    receiver_account_ids = {receiver.account_id for receiver in eligible_receivers}
    account_ids = {sender_account_id, *receiver_account_ids}
    modes = await _route_modes(db, account_ids)
    sender_mode = modes.get(sender_account_id, "nearby")

    route_scoped_receivers = {
        account_id
        for account_id in receiver_account_ids
        if modes.get(account_id, "nearby") == "same_road"
    }
    if sender_mode != "same_road" and not route_scoped_receivers:
        return eligible_receivers

    context_ids = set(route_scoped_receivers)
    context_ids.add(sender_account_id)
    if sender_mode == "same_road":
        context_ids.update(receiver_account_ids)
    contexts = await _fresh_contexts(db, context_ids, now=evaluated_at)
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


async def find_route_eligible_receive_grants(
    db: AsyncSession,
    *,
    sender_account_id: uuid.UUID,
    sender_device_id: uuid.UUID,
    policy: ProximityPolicy,
    now: datetime | None = None,
) -> tuple[EligibleReceiveGrant, ...]:
    """Preserve the accepted proximity query as the first authorization boundary."""
    eligible = await find_eligible_receive_grants(
        db,
        sender_account_id=sender_account_id,
        sender_device_id=sender_device_id,
        policy=policy,
        now=now,
    )
    return await filter_same_road_receive_grants(
        db,
        sender_account_id=sender_account_id,
        eligible_receivers=eligible,
        now=now,
    )
