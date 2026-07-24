import hashlib
import json
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Account, MediaGrant
from app.ptt.provider import (
    MediaProvider,
    MediaProviderError,
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


def utcnow() -> datetime:
    return datetime.now(UTC)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _receive_fingerprint() -> str:
    normalized = json.dumps({"mode": "receive"}, separators=(",", ":"), sort_keys=True)
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
        **_receipt(grant, replayed=False).__dict__,
        server_url=credential.server_url,
        participant_token=credential.participant_token.get_secret_value(),
    )


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

    grant.revoked_at = resolved_now
    grant.outcome_code = "released"
    await db.commit()
    try:
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
