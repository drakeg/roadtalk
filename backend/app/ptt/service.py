import hashlib
import json
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Account, MediaGrant
from app.ptt.provider import (
    MediaProvider,
    MediaProviderError,
    MicrophonePublishRequest,
    ParticipantRequest,
    ReceiveCredentialRequest,
)


class GrantError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ReceiveGrantReceipt:
    grant_id: uuid.UUID
    room_ref: str
    participant_ref: str
    issued_at: datetime
    expires_at: datetime
    policy_version: str
    replayed: bool
    server_url: str | None = None
    participant_token: str | None = None


@dataclass(frozen=True)
class GrantReleaseReceipt:
    grant_id: uuid.UUID
    released_at: datetime
    replayed: bool


@dataclass(frozen=True)
class TransmitGrantReceipt:
    grant_id: uuid.UUID
    receive_grant_id: uuid.UUID
    issued_at: datetime
    expires_at: datetime
    policy_version: str
    replayed: bool


def utcnow() -> datetime:
    return datetime.now(UTC)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _receive_fingerprint() -> str:
    normalized = json.dumps({"mode": "receive"}, separators=(",", ":"), sort_keys=True)
    return _digest(normalized)


def _transmit_fingerprint(receive_grant_id: uuid.UUID) -> str:
    normalized = json.dumps(
        {"mode": "transmit", "receive_grant_id": str(receive_grant_id)},
        separators=(",", ":"),
        sort_keys=True,
    )
    return _digest(normalized)


def _opaque_ref(prefix: str, random_ref: Callable[[], str]) -> str:
    return f"{prefix}_{random_ref()}"


def _receipt(grant: MediaGrant, *, replayed: bool) -> ReceiveGrantReceipt:
    return ReceiveGrantReceipt(
        grant_id=grant.id,
        room_ref=grant.provider_room_ref,
        participant_ref=grant.provider_participant_ref,
        issued_at=grant.issued_at,
        expires_at=grant.expires_at,
        policy_version=grant.policy_version,
        replayed=replayed,
    )


def _transmit_receipt(grant: MediaGrant, *, replayed: bool) -> TransmitGrantReceipt:
    if grant.parent_grant_id is None:
        raise GrantError("PTT_GRANT_INVALID", "The transmit grant is invalid.")
    return TransmitGrantReceipt(
        grant_id=grant.id,
        receive_grant_id=grant.parent_grant_id,
        issued_at=grant.issued_at,
        expires_at=grant.expires_at,
        policy_version=grant.policy_version,
        replayed=replayed,
    )


async def create_receive_grant(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    idempotency_key: str,
    settings: Settings,
    provider: MediaProvider,
    now: datetime | None = None,
    random_ref: Callable[[], str] | None = None,
) -> ReceiveGrantReceipt:
    resolved_now = now or utcnow()
    key_hash = _digest(idempotency_key)
    fingerprint = _receive_fingerprint()
    await db.scalar(select(Account.id).where(Account.id == account_id).with_for_update())

    existing = await db.scalar(
        select(MediaGrant).where(
            MediaGrant.account_id == account_id,
            MediaGrant.grant_kind == "receive",
            MediaGrant.idempotency_key_hash == key_hash,
        )
    )
    if existing is not None:
        if existing.device_id != device_id or existing.request_fingerprint != fingerprint:
            raise GrantError(
                "PTT_IDEMPOTENCY_CONFLICT",
                "The idempotency key was already used for a different request.",
            )
        return _receipt(existing, replayed=True)

    active = await db.scalar(
        select(MediaGrant.id).where(
            MediaGrant.account_id == account_id,
            MediaGrant.device_id == device_id,
            MediaGrant.grant_kind == "receive",
            MediaGrant.revoked_at.is_(None),
            MediaGrant.expires_at > resolved_now,
        )
    )
    if active is not None:
        raise GrantError(
            "PTT_RECEIVE_ALREADY_ACTIVE",
            "Release the active receive grant before creating another.",
        )

    random_source = random_ref or (lambda: secrets.token_urlsafe(18))
    participant_ref = _opaque_ref("pt", random_source)
    expires_at = resolved_now + timedelta(seconds=settings.ptt_receive_grant_ttl_seconds)
    try:
        credential = await provider.issue_receive_credential(
            ReceiveCredentialRequest(
                room_ref=settings.ptt_controlled_room_ref,
                participant_ref=participant_ref,
                ttl_seconds=settings.ptt_receive_grant_ttl_seconds,
            )
        )
    except MediaProviderError as exc:
        raise GrantError(
            "PTT_PROVIDER_UNAVAILABLE",
            "Receive media is not available.",
        ) from exc

    grant = MediaGrant(
        account_id=account_id,
        device_id=device_id,
        grant_kind="receive",
        provider="livekit",
        provider_room_ref=settings.ptt_controlled_room_ref,
        provider_participant_ref=participant_ref,
        action_scope="subscribe",
        policy_version=settings.ptt_policy_version,
        idempotency_key_hash=key_hash,
        request_fingerprint=fingerprint,
        issued_at=resolved_now,
        expires_at=min(expires_at, credential.expires_at),
        outcome_code="issued",
    )
    db.add(grant)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        replay = await db.scalar(
            select(MediaGrant).where(
                MediaGrant.account_id == account_id,
                MediaGrant.grant_kind == "receive",
                MediaGrant.idempotency_key_hash == key_hash,
            )
        )
        if replay is not None and replay.device_id == device_id:
            return _receipt(replay, replayed=True)
        raise GrantError(
            "PTT_GRANT_CONFLICT",
            "The receive grant could not be created.",
        ) from exc
    await db.refresh(grant)
    return ReceiveGrantReceipt(
        grant_id=grant.id,
        room_ref=grant.provider_room_ref,
        participant_ref=grant.provider_participant_ref,
        issued_at=grant.issued_at,
        expires_at=grant.expires_at,
        policy_version=grant.policy_version,
        replayed=False,
        server_url=credential.server_url,
        participant_token=credential.participant_token.get_secret_value(),
    )


async def create_transmit_grant(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    receive_grant_id: uuid.UUID,
    idempotency_key: str,
    settings: Settings,
    provider: MediaProvider,
    now: datetime | None = None,
) -> TransmitGrantReceipt:
    resolved_now = now or utcnow()
    key_hash = _digest(idempotency_key)
    fingerprint = _transmit_fingerprint(receive_grant_id)
    await db.scalar(select(Account.id).where(Account.id == account_id).with_for_update())

    existing = await db.scalar(
        select(MediaGrant).where(
            MediaGrant.account_id == account_id,
            MediaGrant.grant_kind == "transmit",
            MediaGrant.idempotency_key_hash == key_hash,
        )
    )
    if existing is not None:
        if (
            existing.device_id != device_id
            or existing.request_fingerprint != fingerprint
            or existing.revoked_at is not None
            or existing.expires_at <= resolved_now
        ):
            raise GrantError(
                "PTT_IDEMPOTENCY_CONFLICT",
                "The idempotency key cannot authorize this transmit request.",
            )
        return _transmit_receipt(existing, replayed=True)

    receive = await db.scalar(
        select(MediaGrant).where(
            MediaGrant.id == receive_grant_id,
            MediaGrant.account_id == account_id,
            MediaGrant.device_id == device_id,
            MediaGrant.grant_kind == "receive",
            MediaGrant.revoked_at.is_(None),
            MediaGrant.expires_at > resolved_now,
        )
    )
    if receive is None:
        raise GrantError(
            "PTT_RECEIVE_NOT_ACTIVE",
            "An active caller-owned receive grant is required.",
        )

    stale = (
        await db.scalars(
            select(MediaGrant).where(
                MediaGrant.grant_kind == "transmit",
                MediaGrant.revoked_at.is_(None),
                MediaGrant.expires_at <= resolved_now,
                or_(
                    MediaGrant.account_id == account_id,
                    MediaGrant.device_id == device_id,
                ),
            )
        )
    ).all()
    for grant in stale:
        grant.revoked_at = resolved_now
        grant.outcome_code = "expired"

    active = await db.scalar(
        select(MediaGrant.id).where(
            MediaGrant.grant_kind == "transmit",
            MediaGrant.revoked_at.is_(None),
            MediaGrant.expires_at > resolved_now,
            or_(
                MediaGrant.account_id == account_id,
                MediaGrant.device_id == device_id,
            ),
        )
    )
    if active is not None:
        raise GrantError("PTT_TRANSMIT_BUSY", "A publishing grant is already active.")

    grant = MediaGrant(
        account_id=account_id,
        device_id=device_id,
        parent_grant_id=receive.id,
        grant_kind="transmit",
        provider="livekit",
        provider_room_ref=receive.provider_room_ref,
        provider_participant_ref=receive.provider_participant_ref,
        action_scope="microphone_publish",
        policy_version=settings.ptt_policy_version,
        idempotency_key_hash=key_hash,
        request_fingerprint=fingerprint,
        issued_at=resolved_now,
        expires_at=min(
            receive.expires_at,
            resolved_now + timedelta(seconds=settings.ptt_transmit_grant_ttl_seconds),
        ),
        outcome_code="issued",
    )
    room_ref = receive.provider_room_ref
    participant_ref = receive.provider_participant_ref
    db.add(grant)
    try:
        await provider.set_microphone_publish(
            MicrophonePublishRequest(
                room_ref=room_ref,
                participant_ref=participant_ref,
                enabled=True,
            )
        )
        await db.commit()
    except (MediaProviderError, IntegrityError) as exc:
        await db.rollback()
        try:
            await provider.set_microphone_publish(
                MicrophonePublishRequest(
                    room_ref=room_ref,
                    participant_ref=participant_ref,
                    enabled=False,
                )
            )
        except MediaProviderError:
            pass
        raise GrantError(
            "PTT_PROVIDER_UNAVAILABLE",
            "Transmit authorization was denied because provider state is uncertain.",
        ) from exc
    await db.refresh(grant)
    return _transmit_receipt(grant, replayed=False)


async def release_receive_grant(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    grant_id: uuid.UUID,
    provider: MediaProvider,
    now: datetime | None = None,
) -> GrantReleaseReceipt:
    resolved_now = now or utcnow()
    grant = await db.scalar(
        select(MediaGrant)
        .where(
            MediaGrant.id == grant_id,
            MediaGrant.account_id == account_id,
            MediaGrant.device_id == device_id,
            MediaGrant.grant_kind == "receive",
        )
        .with_for_update()
    )
    if grant is None:
        raise GrantError("PTT_GRANT_NOT_FOUND", "The receive grant was not found.")
    if grant.revoked_at is not None:
        return GrantReleaseReceipt(
            grant_id=grant.id,
            released_at=grant.revoked_at,
            replayed=True,
        )

    active_transmits = (
        await db.scalars(
            select(MediaGrant).where(
                MediaGrant.parent_grant_id == grant.id,
                MediaGrant.grant_kind == "transmit",
                MediaGrant.revoked_at.is_(None),
            )
        )
    ).all()
    for transmit in active_transmits:
        transmit.revoked_at = resolved_now
        transmit.outcome_code = "receive_released"
    grant.revoked_at = resolved_now
    grant.outcome_code = "released"
    await db.commit()
    try:
        if active_transmits:
            await provider.set_microphone_publish(
                MicrophonePublishRequest(
                    room_ref=grant.provider_room_ref,
                    participant_ref=grant.provider_participant_ref,
                    enabled=False,
                )
            )
        await provider.remove_participant(
            ParticipantRequest(
                room_ref=grant.provider_room_ref,
                participant_ref=grant.provider_participant_ref,
            )
        )
    except MediaProviderError as exc:
        raise GrantError(
            "PTT_PROVIDER_UNAVAILABLE",
            "The receive grant is locally released; provider cleanup is pending.",
        ) from exc
    return GrantReleaseReceipt(
        grant_id=grant.id,
        released_at=resolved_now,
        replayed=False,
    )


async def release_transmit_grant(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    grant_id: uuid.UUID,
    provider: MediaProvider,
    now: datetime | None = None,
) -> GrantReleaseReceipt:
    resolved_now = now or utcnow()
    grant = await db.scalar(
        select(MediaGrant)
        .where(
            MediaGrant.id == grant_id,
            MediaGrant.account_id == account_id,
            MediaGrant.device_id == device_id,
            MediaGrant.grant_kind == "transmit",
        )
        .with_for_update()
    )
    if grant is None:
        raise GrantError("PTT_GRANT_NOT_FOUND", "The transmit grant was not found.")
    if grant.revoked_at is not None:
        return GrantReleaseReceipt(grant.id, grant.revoked_at, True)

    grant.revoked_at = resolved_now
    grant.outcome_code = "expired" if grant.expires_at <= resolved_now else "released"
    await db.commit()
    try:
        await provider.set_microphone_publish(
            MicrophonePublishRequest(
                room_ref=grant.provider_room_ref,
                participant_ref=grant.provider_participant_ref,
                enabled=False,
            )
        )
    except MediaProviderError as exc:
        raise GrantError(
            "PTT_PROVIDER_UNAVAILABLE",
            "Transmit is locally revoked; provider reconciliation is pending.",
        ) from exc
    return GrantReleaseReceipt(grant.id, resolved_now, False)


async def release_grant(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    grant_id: uuid.UUID,
    provider: MediaProvider,
    now: datetime | None = None,
) -> GrantReleaseReceipt:
    grant_kind = await db.scalar(
        select(MediaGrant.grant_kind).where(
            MediaGrant.id == grant_id,
            MediaGrant.account_id == account_id,
            MediaGrant.device_id == device_id,
        )
    )
    if grant_kind == "receive":
        return await release_receive_grant(
            db,
            account_id=account_id,
            device_id=device_id,
            grant_id=grant_id,
            provider=provider,
            now=now,
        )
    if grant_kind == "transmit":
        return await release_transmit_grant(
            db,
            account_id=account_id,
            device_id=device_id,
            grant_id=grant_id,
            provider=provider,
            now=now,
        )
    raise GrantError("PTT_GRANT_NOT_FOUND", "The grant was not found.")


async def revoke_device_transmit_grants(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    reason: str,
    now: datetime | None = None,
) -> None:
    resolved_now = now or utcnow()
    await db.execute(
        update(MediaGrant)
        .where(
            MediaGrant.account_id == account_id,
            MediaGrant.device_id == device_id,
            MediaGrant.grant_kind == "transmit",
            MediaGrant.revoked_at.is_(None),
        )
        .values(revoked_at=resolved_now, outcome_code=reason)
    )
