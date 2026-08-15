import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import case, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.constants import GENERAL_CHANNEL_ID
from app.db.models import Account, Channel, ChannelMembership, ChannelSelection, MediaGrant


class ChannelError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ChannelSummary:
    id: uuid.UUID
    slug: str | None
    display_label: str
    type: str
    selected: bool
    enabled: bool
    version: int


@dataclass(frozen=True)
class ChannelSelectionReceipt(ChannelSummary):
    selected_at: datetime
    selection_version: int


async def _authorized_channel(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    channel_id: uuid.UUID,
) -> Channel | None:
    active_membership = exists().where(
        ChannelMembership.account_id == account_id,
        ChannelMembership.channel_id == Channel.id,
        ChannelMembership.state == "active",
    )
    return cast(
        Channel | None,
        await db.scalar(
            select(Channel).where(
                Channel.id == channel_id,
                Channel.enabled.is_(True),
                Channel.closed_at.is_(None),
                or_(Channel.channel_type == "public", active_membership),
            )
        ),
    )


async def _ensure_selection(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    now: datetime,
    commit: bool = True,
) -> tuple[ChannelSelection, Channel]:
    account = await db.scalar(select(Account).where(Account.id == account_id).with_for_update())
    if account is None or account.status != "active":
        raise ChannelError("CHANNEL_ACCOUNT_INVALID", "The channel selection is unavailable.")

    selection = await db.scalar(
        select(ChannelSelection).where(ChannelSelection.account_id == account_id)
    )
    channel = None
    if selection is not None:
        channel = await _authorized_channel(
            db,
            account_id=account_id,
            channel_id=selection.channel_id,
        )
    if selection is None:
        selection = ChannelSelection(
            account_id=account_id,
            channel_id=GENERAL_CHANNEL_ID,
            selected_at=now,
            version=1,
        )
        db.add(selection)
    elif channel is None:
        selection.channel_id = GENERAL_CHANNEL_ID
        selection.selected_at = now
        selection.version += 1

    if channel is None:
        channel = await db.scalar(
            select(Channel).where(
                Channel.id == GENERAL_CHANNEL_ID,
                Channel.enabled.is_(True),
                Channel.closed_at.is_(None),
            )
        )
    if channel is None:
        raise ChannelError("CHANNEL_DEFAULT_UNAVAILABLE", "The default channel is unavailable.")
    if commit:
        await db.commit()
    return selection, channel


def _summary(channel: Channel, selected_channel_id: uuid.UUID) -> ChannelSummary:
    return ChannelSummary(
        id=channel.id,
        slug=channel.stable_slug,
        display_label=channel.display_label,
        type=channel.channel_type,
        selected=channel.id == selected_channel_id,
        enabled=channel.enabled,
        version=channel.version,
    )


async def list_channels(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    now: datetime | None = None,
) -> tuple[ChannelSummary, ...]:
    resolved_now = now or datetime.now(UTC)
    selection, _ = await _ensure_selection(db, account_id=account_id, now=resolved_now)
    active_membership = exists().where(
        ChannelMembership.account_id == account_id,
        ChannelMembership.channel_id == Channel.id,
        ChannelMembership.state == "active",
    )
    public_order = case(
        (Channel.stable_slug == "general", 0),
        (Channel.stable_slug == "rv", 1),
        else_=2,
    )
    channels = (
        await db.scalars(
            select(Channel)
            .where(
                Channel.enabled.is_(True),
                Channel.closed_at.is_(None),
                or_(Channel.channel_type == "public", active_membership),
            )
            .order_by(public_order, Channel.display_label, Channel.id)
        )
    ).all()
    return tuple(_summary(channel, selection.channel_id) for channel in channels)


async def get_current_channel(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    now: datetime | None = None,
) -> ChannelSelectionReceipt:
    resolved_now = now or datetime.now(UTC)
    selection, channel = await _ensure_selection(db, account_id=account_id, now=resolved_now)
    summary = _summary(channel, selection.channel_id)
    return ChannelSelectionReceipt(
        **summary.__dict__,
        selected_at=selection.selected_at,
        selection_version=selection.version,
    )


async def select_channel(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    channel_id: uuid.UUID,
    now: datetime | None = None,
) -> ChannelSelectionReceipt:
    resolved_now = now or datetime.now(UTC)
    selection, current = await _ensure_selection(
        db,
        account_id=account_id,
        now=resolved_now,
        commit=False,
    )
    target = await _authorized_channel(db, account_id=account_id, channel_id=channel_id)
    if target is None:
        await db.rollback()
        raise ChannelError("CHANNEL_NOT_AVAILABLE", "The channel is not available.")

    if selection.channel_id != channel_id:
        active_grant = await db.scalar(
            select(MediaGrant.id).where(
                MediaGrant.account_id == account_id,
                MediaGrant.revoked_at.is_(None),
                MediaGrant.expires_at > resolved_now,
            )
        )
        if active_grant is not None:
            await db.rollback()
            raise ChannelError(
                "CHANNEL_MEDIA_ACTIVE",
                "Release active media before changing channels.",
            )
        selection.channel_id = target.id
        selection.selected_at = resolved_now
        selection.version += 1
    else:
        target = current
    await db.commit()

    summary = _summary(target, selection.channel_id)
    return ChannelSelectionReceipt(
        **summary.__dict__,
        selected_at=selection.selected_at,
        selection_version=selection.version,
    )
