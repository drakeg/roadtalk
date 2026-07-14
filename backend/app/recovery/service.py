import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_refresh_token, new_refresh_token
from app.auth.service import token_pair, utcnow
from app.config import Settings
from app.db.models import Account, Device, Profile, RecoveryCredential, Session
from app.recovery.schemas import RecoveryKeyResponse, RecoverySessionResponse
from app.recovery.security import (
    DUMMY_RECOVERY_HASH,
    hash_recovery_key,
    new_recovery_key,
    recovery_key_id,
    verify_recovery_key,
)


class RecoveryError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def recovery_failed() -> RecoveryError:
    return RecoveryError(
        "RECOVERY_FAILED",
        "The account could not be recovered with that key.",
    )


async def create_or_rotate_recovery_key(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    settings: Settings,
    now: datetime | None = None,
) -> RecoveryKeyResponse:
    issued = new_recovery_key()
    encoded = await asyncio.to_thread(
        hash_recovery_key,
        issued.raw,
        settings.recovery_key_pepper.get_secret_value(),
    )
    changed_at = now or utcnow()
    credential = await db.scalar(
        select(RecoveryCredential)
        .where(RecoveryCredential.account_id == account_id)
        .with_for_update()
    )
    if credential is None:
        credential = RecoveryCredential(
            account_id=account_id,
            key_id=issued.key_id,
            key_hash=encoded,
            rotated_at=changed_at,
        )
        db.add(credential)
    else:
        credential.key_id = issued.key_id
        credential.key_hash = encoded
        credential.rotated_at = changed_at
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise RecoveryError(
            "RECOVERY_KEY_CONFLICT",
            "A recovery key could not be issued. Try again.",
        ) from exc
    return RecoveryKeyResponse(recovery_key=issued.raw)


async def recover_account(
    db: AsyncSession,
    *,
    raw_key: str,
    installation_id: str,
    platform: str,
    settings: Settings,
    now: datetime | None = None,
) -> RecoverySessionResponse:
    pepper = settings.recovery_key_pepper.get_secret_value()
    key_id = recovery_key_id(raw_key)
    credential: RecoveryCredential | None = None
    if key_id is not None:
        credential = await db.scalar(
            select(RecoveryCredential)
            .where(RecoveryCredential.key_id == key_id)
            .with_for_update()
        )

    encoded = credential.key_hash if credential is not None else DUMMY_RECOVERY_HASH
    valid = await asyncio.to_thread(verify_recovery_key, raw_key, encoded, pepper)
    if credential is None or not valid:
        raise recovery_failed()

    account = await db.scalar(
        select(Account)
        .where(Account.id == credential.account_id)
        .with_for_update()
    )
    if account is None or account.status != "active":
        raise recovery_failed()

    device = await db.scalar(
        select(Device)
        .where(Device.installation_id == installation_id)
        .with_for_update()
    )
    if device is not None and device.platform != platform:
        raise recovery_failed()

    changed_at = now or utcnow()
    source_account_id: uuid.UUID | None = None
    if device is None:
        device = Device(
            account_id=account.id,
            platform=platform,
            installation_id=installation_id,
            last_seen_at=changed_at,
        )
        db.add(device)
        await db.flush()
    elif device.account_id != account.id:
        source_account_id = device.account_id
        if not await _temporary_account_is_transferable(
            db,
            account_id=source_account_id,
            device_id=device.id,
        ):
            raise recovery_failed()
        device.account_id = account.id
        device.last_seen_at = changed_at
        await db.flush()

    await db.execute(
        update(Session)
        .where(
            Session.account_id == account.id,
            Session.revoked_at.is_(None),
        )
        .values(revoked_at=changed_at, revoke_reason="account_recovered")
    )
    if source_account_id is not None:
        await db.execute(
            update(Session)
            .where(
                Session.account_id == source_account_id,
                Session.revoked_at.is_(None),
            )
            .values(revoked_at=changed_at, revoke_reason="account_recovered")
        )

    replacement_key = new_recovery_key()
    replacement_hash = await asyncio.to_thread(
        hash_recovery_key,
        replacement_key.raw,
        pepper,
    )
    credential.key_id = replacement_key.key_id
    credential.key_hash = replacement_hash
    credential.rotated_at = changed_at

    refresh_token = new_refresh_token()
    session = Session(
        account_id=account.id,
        device_id=device.id,
        refresh_token_hash=hash_refresh_token(
            refresh_token,
            settings.refresh_token_pepper.get_secret_value(),
        ),
        expires_at=changed_at + timedelta(seconds=settings.refresh_token_ttl_seconds),
    )
    db.add(session)

    if source_account_id is not None:
        await db.execute(delete(Account).where(Account.id == source_account_id))

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise recovery_failed() from exc
    await db.refresh(session)
    pair = token_pair(session, refresh_token, settings)
    return RecoverySessionResponse(
        **pair.model_dump(),
        account_id=account.id,
        device_id=device.id,
        session_id=session.id,
        recovery_key=replacement_key.raw,
    )


async def _temporary_account_is_transferable(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
) -> bool:
    account = await db.scalar(
        select(Account).where(Account.id == account_id).with_for_update()
    )
    if (
        account is None
        or account.status != "active"
        or account.account_type != "anonymous"
    ):
        return False
    profile = await db.scalar(
        select(Profile.account_id).where(Profile.account_id == account_id)
    )
    recovery = await db.scalar(
        select(RecoveryCredential.account_id).where(
            RecoveryCredential.account_id == account_id
        )
    )
    other_device = await db.scalar(
        select(Device.id).where(
            Device.account_id == account_id,
            Device.id != device_id,
        )
    )
    return profile is None and recovery is None and other_device is None
