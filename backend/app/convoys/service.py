import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Account, Convoy, ConvoyMembership


class ConvoyLifecycleError(ValueError):
    pass


async def create_convoy(
    db: AsyncSession, *, leader: Account, display_name: str
) -> tuple[Convoy, ConvoyMembership]:
    if leader.status != "active":
        raise ConvoyLifecycleError("active account required")

    convoy = Convoy(leader_account_id=leader.id, display_name=display_name)
    membership = ConvoyMembership(
        convoy=convoy, account_id=leader.id, role="leader", state="active"
    )
    db.add(convoy)
    db.add(membership)
    await db.commit()
    await db.refresh(convoy)
    await db.refresh(membership)
    return convoy, membership


async def join_convoy(
    db: AsyncSession, *, convoy_id: uuid.UUID, account: Account
) -> ConvoyMembership:
    if account.status != "active":
        raise ConvoyLifecycleError("active account required")

    convoy = await db.get(Convoy, convoy_id, with_for_update=True)
    if convoy is None or convoy.state != "active":
        raise ConvoyLifecycleError("convoy unavailable")

    existing = await db.scalar(
        select(ConvoyMembership).where(
            ConvoyMembership.convoy_id == convoy_id,
            ConvoyMembership.account_id == account.id,
        )
    )
    if existing is not None:
        if existing.state == "active":
            return existing
        raise ConvoyLifecycleError("membership unavailable")

    membership = ConvoyMembership(
        convoy_id=convoy_id, account_id=account.id, role="member", state="active"
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


async def end_membership(
    db: AsyncSession,
    *,
    membership_id: uuid.UUID,
    account_id: uuid.UUID,
    state: str,
) -> ConvoyMembership:
    if state not in {"left", "revoked", "expired"}:
        raise ConvoyLifecycleError("invalid terminal membership state")

    membership = await db.get(ConvoyMembership, membership_id, with_for_update=True)
    if (
        membership is None
        or membership.account_id != account_id
        or membership.state != "active"
        or membership.role == "leader"
    ):
        raise ConvoyLifecycleError("membership unavailable")

    membership.state = state
    membership.ended_at = datetime.now(UTC)
    membership.version += 1
    await db.commit()
    await db.refresh(membership)
    return membership


async def disband_convoy(
    db: AsyncSession, *, convoy_id: uuid.UUID, leader_account_id: uuid.UUID
) -> Convoy:
    convoy = await db.get(Convoy, convoy_id, with_for_update=True)
    if convoy is None or convoy.leader_account_id != leader_account_id or convoy.state != "active":
        raise ConvoyLifecycleError("convoy unavailable")

    now = datetime.now(UTC)
    memberships = (
        await db.scalars(
            select(ConvoyMembership).where(
                ConvoyMembership.convoy_id == convoy_id,
                ConvoyMembership.state == "active",
            )
        )
    ).all()
    for membership in memberships:
        membership.state = "revoked"
        membership.ended_at = now
        membership.version += 1

    convoy.state = "disbanded"
    convoy.disbanded_at = now
    convoy.version += 1
    await db.commit()
    await db.refresh(convoy)
    return convoy
