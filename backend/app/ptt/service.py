import hashlib
import json
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, Protocol

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import Account, MediaGrant
from app.ptt.provider import (
    MediaProvider,
    MediaProviderError,
    MediaProviderTrackVerificationError,
    MicrophonePublishRequest,
    MicrophoneTrackLookupRequest,
    ParticipantRequest,
    ReceiveCredentialRequest,
    SelectiveSubscriptionRequest,
)
from app.ptt.proximity import (
    EligibleReceiveGrant,
    ProximityEligibilityError,
    ProximityPolicy,
    find_eligible_receive_grants,
    proximity_policy_from_settings,
)


class GrantError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class ProximityEligibilityFinder(Protocol):
    async def __call__(
        self,
        db: AsyncSession,
        *,
        sender_account_id: uuid.UUID,
        sender_device_id: uuid.UUID,
        policy: ProximityPolicy,
        now: datetime | None = None,
    ) -> tuple[EligibleReceiveGrant, ...]: ...


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


@dataclass(frozen=True)
class PublicationReceipt:
    transmit_grant_id: uuid.UUID
    delivery_state: Literal["ready", "no_nearby_listeners", "reconciling", "ended"]
    proximity_policy_version: str
    evaluated_at: datetime
    expires_at: datetime
    replayed: bool


@dataclass(frozen=True)
class MediaReconciliationReceipt:
    grants_examined: int
    grants_locally_revoked: int
    participants_reconciled: int
    participants_pending: int


_PROVIDER_CLEANUP_OUTCOMES = {
    "provider_cleanup_pending",
    "session_revoked",
    "device_revoked",
    "account_revoked",
}


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


def _publication_receipt(
    grant: MediaGrant,
    *,
    replayed: bool,
    now: datetime,
) -> PublicationReceipt:
    if grant.proximity_policy_version is None or grant.eligibility_evaluated_at is None:
        raise GrantError("PTT_PUBLICATION_INVALID", "The publication state is invalid.")
    if grant.revoked_at is not None or grant.expires_at <= now:
        delivery_state: Literal["ready", "no_nearby_listeners", "reconciling", "ended"] = "ended"
    elif grant.outcome_code == "delivery_ready":
        delivery_state = "ready"
    elif grant.outcome_code == "no_nearby_listeners":
        delivery_state = "no_nearby_listeners"
    else:
        delivery_state = "reconciling"
    return PublicationReceipt(
        transmit_grant_id=grant.id,
        delivery_state=delivery_state,
        proximity_policy_version=grant.proximity_policy_version,
        evaluated_at=grant.eligibility_evaluated_at,
        expires_at=grant.expires_at,
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
    eligibility_finder: ProximityEligibilityFinder = find_eligible_receive_grants,
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

    try:
        eligible_receivers = await eligibility_finder(
            db,
            sender_account_id=account_id,
            sender_device_id=device_id,
            policy=proximity_policy_from_settings(settings),
            now=resolved_now,
        )
    except ProximityEligibilityError as exc:
        raise GrantError("PTT_LOCATION_UNAVAILABLE", exc.detail) from exc
    if not eligible_receivers:
        raise GrantError(
            "PTT_NO_NEARBY_LISTENERS",
            "No nearby listeners are currently available.",
        )

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
    receive_id = receive.id
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
        await db.execute(
            update(MediaGrant)
            .where(
                MediaGrant.id == receive_id,
                MediaGrant.revoked_at.is_(None),
            )
            .values(
                revoked_at=resolved_now,
                outcome_code="provider_cleanup_pending",
            )
        )
        await db.commit()
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
        try:
            await provider.remove_participant(
                ParticipantRequest(
                    room_ref=room_ref,
                    participant_ref=participant_ref,
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


async def publish_transmit_track(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    transmit_grant_id: uuid.UUID,
    track_ref: str,
    settings: Settings,
    provider: MediaProvider,
    eligibility_finder: ProximityEligibilityFinder = find_eligible_receive_grants,
    now: datetime | None = None,
) -> PublicationReceipt:
    resolved_now = now or utcnow()
    await db.scalar(select(Account.id).where(Account.id == account_id).with_for_update())
    grant = await db.scalar(
        select(MediaGrant)
        .where(
            MediaGrant.id == transmit_grant_id,
            MediaGrant.account_id == account_id,
            MediaGrant.device_id == device_id,
            MediaGrant.grant_kind == "transmit",
        )
        .with_for_update()
    )
    if grant is None:
        raise GrantError("PTT_TRANSMIT_NOT_FOUND", "The transmit grant was not found.")

    if grant.provider_track_ref is not None:
        if grant.provider_track_ref != track_ref:
            raise GrantError(
                "PTT_PUBLICATION_CONFLICT",
                "A different track was already submitted for this transmission.",
            )
        return _publication_receipt(grant, replayed=True, now=resolved_now)

    if grant.revoked_at is not None or grant.expires_at <= resolved_now:
        raise GrantError("PTT_TRANSMIT_NOT_ACTIVE", "An active transmit grant is required.")

    try:
        verified_track = await provider.verify_microphone_track(
            MicrophoneTrackLookupRequest(
                room_ref=grant.provider_room_ref,
                participant_ref=grant.provider_participant_ref,
                track_ref=track_ref,
            )
        )
    except MediaProviderTrackVerificationError as exc:
        raise GrantError(
            "PTT_TRACK_INVALID",
            "The microphone publication could not be verified.",
        ) from exc
    except MediaProviderError as exc:
        raise GrantError(
            "PTT_PROVIDER_UNAVAILABLE",
            "Publication verification is unavailable.",
        ) from exc

    policy = proximity_policy_from_settings(settings)
    try:
        eligible_receivers = await eligibility_finder(
            db,
            sender_account_id=account_id,
            sender_device_id=device_id,
            policy=policy,
            now=resolved_now,
        )
    except ProximityEligibilityError as exc:
        raise GrantError("PTT_LOCATION_UNAVAILABLE", exc.detail) from exc

    grant.provider_track_ref = verified_track.track_ref
    grant.proximity_policy_version = policy.version
    grant.eligibility_evaluated_at = resolved_now
    if not eligible_receivers:
        grant.outcome_code = "no_nearby_listeners"
        await db.commit()
        await db.refresh(grant)
        return _publication_receipt(grant, replayed=False, now=resolved_now)

    participant_refs = tuple(sorted({receiver.participant_ref for receiver in eligible_receivers}))
    subscribe_request = SelectiveSubscriptionRequest(
        track=verified_track,
        participant_refs=participant_refs,
        action="subscribe",
    )
    unsubscribe_request = SelectiveSubscriptionRequest(
        track=verified_track,
        participant_refs=participant_refs,
        action="unsubscribe",
    )
    try:
        await provider.update_track_subscriptions(subscribe_request)
        grant.outcome_code = "delivery_ready"
        await db.commit()
    except MediaProviderError as exc:
        try:
            await provider.update_track_subscriptions(unsubscribe_request)
        except MediaProviderError:
            pass
        grant.outcome_code = "delivery_reconciling"
        await db.commit()
        raise GrantError(
            "PTT_PROVIDER_UNAVAILABLE",
            "Nearby delivery could not be confirmed.",
        ) from exc
    except IntegrityError as exc:
        await db.rollback()
        try:
            await provider.update_track_subscriptions(unsubscribe_request)
        except MediaProviderError:
            pass
        await db.execute(
            update(MediaGrant)
            .where(MediaGrant.id == transmit_grant_id)
            .values(
                provider_track_ref=verified_track.track_ref,
                proximity_policy_version=policy.version,
                eligibility_evaluated_at=resolved_now,
                outcome_code="delivery_reconciling",
            )
        )
        await db.commit()
        raise GrantError(
            "PTT_PROVIDER_UNAVAILABLE",
            "Nearby delivery could not be confirmed.",
        ) from exc
    await db.refresh(grant)
    return _publication_receipt(grant, replayed=False, now=resolved_now)


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
    cleanup_error: MediaProviderError | None = None
    if active_transmits:
        try:
            await provider.set_microphone_publish(
                MicrophonePublishRequest(
                    room_ref=grant.provider_room_ref,
                    participant_ref=grant.provider_participant_ref,
                    enabled=False,
                )
            )
        except MediaProviderError as exc:
            cleanup_error = exc
    try:
        await provider.remove_participant(
            ParticipantRequest(
                room_ref=grant.provider_room_ref,
                participant_ref=grant.provider_participant_ref,
            )
        )
    except MediaProviderError as exc:
        cleanup_error = cleanup_error or exc
    if cleanup_error is not None:
        grant.outcome_code = "provider_cleanup_pending"
        await db.commit()
        raise GrantError(
            "PTT_PROVIDER_UNAVAILABLE",
            "The receive grant is locally released; provider cleanup is pending.",
        ) from cleanup_error
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
        grant.outcome_code = "provider_cleanup_pending"
        if grant.parent_grant_id is not None:
            await db.execute(
                update(MediaGrant)
                .where(
                    MediaGrant.id == grant.parent_grant_id,
                    MediaGrant.revoked_at.is_(None),
                )
                .values(
                    revoked_at=resolved_now,
                    outcome_code="provider_cleanup_pending",
                )
            )
        await db.commit()
        try:
            await provider.remove_participant(
                ParticipantRequest(
                    room_ref=grant.provider_room_ref,
                    participant_ref=grant.provider_participant_ref,
                )
            )
        except MediaProviderError:
            pass
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


async def revoke_device_media_grants(
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
            MediaGrant.revoked_at.is_(None),
        )
        .values(revoked_at=resolved_now, outcome_code=reason)
    )


async def reconcile_media_grants(
    db: AsyncSession,
    *,
    provider: MediaProvider,
    now: datetime | None = None,
    limit: int = 100,
) -> MediaReconciliationReceipt:
    """Fail closed locally, then retry bounded provider cleanup.

    This routine is deliberately transport-agnostic and unscheduled. D07 tests inject
    the deterministic fake; a future approved operator path may invoke it without
    adding a queue, worker, cloud resource, or background provider call to CI.
    """
    if limit < 1 or limit > 1_000:
        raise ValueError("media reconciliation limit must be between 1 and 1000")

    resolved_now = now or utcnow()
    grants = (
        await db.scalars(
            select(MediaGrant)
            .where(
                or_(
                    and_(
                        MediaGrant.revoked_at.is_(None),
                        MediaGrant.expires_at <= resolved_now,
                    ),
                    MediaGrant.outcome_code.in_(_PROVIDER_CLEANUP_OUTCOMES),
                )
            )
            .order_by(MediaGrant.expires_at, MediaGrant.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
    ).all()

    locally_revoked = 0
    participants: dict[tuple[str, str], list[MediaGrant]] = {}
    for grant in grants:
        if grant.revoked_at is None:
            grant.revoked_at = resolved_now
            grant.outcome_code = "expired"
            locally_revoked += 1
        participants.setdefault(
            (grant.provider_room_ref, grant.provider_participant_ref), []
        ).append(grant)
    await db.commit()

    reconciled = 0
    pending = 0
    for (room_ref, participant_ref), participant_grants in participants.items():
        cleanup_failed = False
        try:
            await provider.set_microphone_publish(
                MicrophonePublishRequest(
                    room_ref=room_ref,
                    participant_ref=participant_ref,
                    enabled=False,
                )
            )
        except MediaProviderError:
            cleanup_failed = True
        should_remove = any(
            grant.grant_kind == "receive" or grant.outcome_code in _PROVIDER_CLEANUP_OUTCOMES
            for grant in participant_grants
        )
        if should_remove:
            try:
                await provider.remove_participant(
                    ParticipantRequest(
                        room_ref=room_ref,
                        participant_ref=participant_ref,
                    )
                )
            except MediaProviderError:
                cleanup_failed = True
        if cleanup_failed:
            pending += 1
            for grant in participant_grants:
                grant.outcome_code = "provider_cleanup_pending"
        else:
            reconciled += 1
            for grant in participant_grants:
                if grant.outcome_code in _PROVIDER_CLEANUP_OUTCOMES:
                    grant.outcome_code = "provider_reconciled"

    await db.commit()
    return MediaReconciliationReceipt(
        grants_examined=len(grants),
        grants_locally_revoked=locally_revoked,
        participants_reconciled=reconciled,
        participants_pending=pending,
    )
