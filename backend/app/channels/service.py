import hashlib
import re
import secrets
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.constants import GENERAL_CHANNEL_ID
from app.channels.security import (
    DUMMY_INVITE_HASH,
    hash_invite,
    invite_fingerprint,
    new_invite,
    verify_invite,
)
from app.config import Settings
from app.db.models import (
    Account,
    Channel,
    ChannelInvite,
    ChannelMembership,
    ChannelSelection,
    MediaGrant,
)
from app.ptt.service import revoke_channel_media_grants


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


@dataclass(frozen=True)
class PrivateChannelReceipt(ChannelSummary):
    created_at: datetime
    invite: str | None = None
    replayed: bool = False


@dataclass(frozen=True)
class ChannelLifecycleReceipt:
    channel_id: uuid.UUID
    state: str
    changed_at: datetime
    replayed: bool


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized or len(normalized) > 64 or any(ord(char) < 32 for char in normalized):
        raise ChannelError("CHANNEL_LABEL_INVALID", "The channel label is invalid.")
    return normalized


def _private_receipt(
    channel: Channel, *, invite: str | None = None, replayed: bool = False
) -> PrivateChannelReceipt:
    return PrivateChannelReceipt(
        id=channel.id,
        slug=None,
        display_label=channel.display_label,
        type="private",
        selected=False,
        enabled=channel.enabled,
        version=channel.version,
        created_at=channel.created_at,
        invite=invite,
        replayed=replayed,
    )


async def create_private_channel(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    display_label: str,
    idempotency_key: str,
    settings: Settings,
) -> PrivateChannelReceipt:  # pragma: no cover - exercised by opt-in PostgreSQL suite
    label = _normalize_label(display_label)
    account = await db.scalar(select(Account).where(Account.id == account_id).with_for_update())
    if account is None or account.status != "active":
        raise ChannelError("CHANNEL_ACCOUNT_INVALID", "The private channel is unavailable.")
    key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
    request_fingerprint = hashlib.sha256(label.encode()).hexdigest()
    replay = await db.scalar(
        select(Channel).where(
            Channel.creator_account_id == account_id,
            Channel.create_idempotency_hash == key_hash,
        )
    )
    if replay is not None:
        if replay.create_request_fingerprint != request_fingerprint:
            raise ChannelError("CHANNEL_IDEMPOTENCY_CONFLICT", "The idempotency key conflicts.")
        return _private_receipt(replay, replayed=True)
    count = await db.scalar(
        select(Channel)
        .where(
            Channel.creator_account_id == account_id,
            Channel.channel_type == "private",
            Channel.closed_at.is_(None),
        )
        .with_only_columns(func.count())
    )
    if int(count or 0) >= settings.channel_private_limit:
        raise ChannelError("CHANNEL_PRIVATE_LIMIT", "The private channel limit was reached.")
    raw_invite = new_invite()
    channel = Channel(
        display_label=label,
        channel_type="private",
        enabled=True,
        creator_account_id=account_id,
        provider_room_ref=f"rm_v1_{secrets.token_urlsafe(18)}",
        policy_version="channel-v1",
        version=1,
        create_idempotency_hash=key_hash,
        create_request_fingerprint=request_fingerprint,
    )
    db.add(channel)
    await db.flush()
    db.add_all(
        [
            ChannelMembership(account_id=account_id, channel_id=channel.id),
            ChannelInvite(
                channel_id=channel.id,
                secret_hash=hash_invite(
                    raw_invite, settings.channel_invite_pepper.get_secret_value()
                ),
                fingerprint=invite_fingerprint(raw_invite),
            ),
        ]
    )
    await db.commit()
    await db.refresh(channel)
    return _private_receipt(channel, invite=raw_invite)


async def join_private_channel(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    raw_invite: str,
    settings: Settings,
    now: datetime | None = None,
) -> ChannelLifecycleReceipt:  # pragma: no cover - exercised by opt-in PostgreSQL suite
    resolved_now = now or datetime.now(UTC)
    fingerprint = invite_fingerprint(raw_invite)
    candidates = (
        await db.scalars(
            select(ChannelInvite)
            .join(Channel)
            .where(
                ChannelInvite.fingerprint == fingerprint,
                ChannelInvite.revoked_at.is_(None),
                Channel.enabled.is_(True),
                Channel.closed_at.is_(None),
                Channel.channel_type == "private",
            )
        )
    ).all()
    invite = next(
        (
            item
            for item in candidates
            if verify_invite(
                raw_invite, item.secret_hash, settings.channel_invite_pepper.get_secret_value()
            )
        ),
        None,
    )
    if invite is None:
        verify_invite(raw_invite, DUMMY_INVITE_HASH, "")
        raise ChannelError("CHANNEL_INVITE_INVALID", "The channel invite is invalid.")
    membership = await db.scalar(
        select(ChannelMembership).where(
            ChannelMembership.account_id == account_id,
            ChannelMembership.channel_id == invite.channel_id,
        )
    )
    replayed = membership is not None and membership.state == "active"
    if membership is None:
        db.add(
            ChannelMembership(
                account_id=account_id, channel_id=invite.channel_id, joined_at=resolved_now
            )
        )
    elif not replayed:
        membership.state = "active"
        membership.joined_at = resolved_now
        membership.left_at = None
        membership.version += 1
    invite.last_used_at = resolved_now
    await db.commit()
    return ChannelLifecycleReceipt(invite.channel_id, "joined", resolved_now, replayed)


async def leave_private_channel(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    channel_id: uuid.UUID,
    now: datetime | None = None,
) -> ChannelLifecycleReceipt:  # pragma: no cover - exercised by opt-in PostgreSQL suite
    resolved_now = now or datetime.now(UTC)
    membership = await db.scalar(
        select(ChannelMembership)
        .join(Channel)
        .where(
            ChannelMembership.account_id == account_id,
            ChannelMembership.channel_id == channel_id,
            Channel.channel_type == "private",
            Channel.closed_at.is_(None),
        )
        .with_for_update()
    )
    if membership is None:
        raise ChannelError("CHANNEL_NOT_AVAILABLE", "The channel is not available.")
    replayed = membership.state == "left"
    if not replayed:
        await revoke_channel_media_grants(
            db,
            account_id=account_id,
            channel_id=channel_id,
            reason="channel_left",
            now=resolved_now,
        )
        membership.state = "left"
        membership.left_at = resolved_now
        membership.version += 1
        selection = await db.scalar(
            select(ChannelSelection).where(ChannelSelection.account_id == account_id)
        )
        if selection is not None and selection.channel_id == channel_id:
            selection.channel_id = GENERAL_CHANNEL_ID
            selection.selected_at = resolved_now
            selection.version += 1
    await db.commit()
    return ChannelLifecycleReceipt(channel_id, "left", membership.left_at or resolved_now, replayed)


async def rotate_private_invite(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    channel_id: uuid.UUID,
    idempotency_key: str,
    settings: Settings,
    now: datetime | None = None,
) -> PrivateChannelReceipt:  # pragma: no cover - exercised by opt-in PostgreSQL suite
    resolved_now = now or datetime.now(UTC)
    channel = await db.scalar(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.creator_account_id == account_id,
            Channel.channel_type == "private",
            Channel.closed_at.is_(None),
            Channel.enabled.is_(True),
        )
    )
    if channel is None:
        raise ChannelError("CHANNEL_NOT_AVAILABLE", "The channel is not available.")
    invite = await db.scalar(
        select(ChannelInvite).where(ChannelInvite.channel_id == channel_id).with_for_update()
    )
    if invite is None:
        raise ChannelError("CHANNEL_NOT_AVAILABLE", "The channel is not available.")
    key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
    if invite.rotation_idempotency_hash == key_hash:
        return _private_receipt(channel, replayed=True)
    raw_invite = new_invite()
    invite.secret_hash = hash_invite(raw_invite, settings.channel_invite_pepper.get_secret_value())
    invite.fingerprint = invite_fingerprint(raw_invite)
    invite.rotated_at = resolved_now
    invite.last_used_at = None
    invite.version += 1
    invite.rotation_idempotency_hash = key_hash
    channel.version += 1
    await db.commit()
    return _private_receipt(channel, invite=raw_invite)


async def close_private_channel(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    channel_id: uuid.UUID,
    now: datetime | None = None,
) -> ChannelLifecycleReceipt:  # pragma: no cover - exercised by opt-in PostgreSQL suite
    resolved_now = now or datetime.now(UTC)
    channel = await db.scalar(
        select(Channel)
        .where(
            Channel.id == channel_id,
            Channel.creator_account_id == account_id,
            Channel.channel_type == "private",
        )
        .with_for_update()
    )
    if channel is None:
        raise ChannelError("CHANNEL_NOT_AVAILABLE", "The channel is not available.")
    replayed = channel.closed_at is not None
    if not replayed:
        await revoke_channel_media_grants(
            db,
            channel_id=channel_id,
            reason="channel_closed",
            now=resolved_now,
        )
        selections = (
            await db.scalars(
                select(ChannelSelection).where(ChannelSelection.channel_id == channel_id)
            )
        ).all()
        for selection in selections:
            selection.channel_id = GENERAL_CHANNEL_ID
            selection.selected_at = resolved_now
            selection.version += 1
        memberships = (
            await db.scalars(
                select(ChannelMembership).where(
                    ChannelMembership.channel_id == channel_id, ChannelMembership.state == "active"
                )
            )
        ).all()
        for membership in memberships:
            membership.state = "left"
            membership.left_at = resolved_now
            membership.version += 1
        invite = await db.scalar(
            select(ChannelInvite).where(ChannelInvite.channel_id == channel_id)
        )
        if invite is not None:
            invite.revoked_at = resolved_now
            invite.version += 1
        channel.enabled = False
        channel.closed_at = resolved_now
        channel.version += 1
    await db.commit()
    return ChannelLifecycleReceipt(
        channel_id, "closed", channel.closed_at or resolved_now, replayed
    )


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
        active_transmit = await db.scalar(
            select(MediaGrant.id).where(
                MediaGrant.account_id == account_id,
                MediaGrant.channel_id == selection.channel_id,
                MediaGrant.grant_kind == "transmit",
                MediaGrant.revoked_at.is_(None),
                MediaGrant.expires_at > resolved_now,
            )
        )
        if active_transmit is not None:
            await db.rollback()
            raise ChannelError(
                "CHANNEL_MEDIA_ACTIVE",
                "End the active transmission before changing channels.",
            )
        await revoke_channel_media_grants(
            db,
            account_id=account_id,
            channel_id=selection.channel_id,
            reason="channel_switched",
            now=resolved_now,
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
