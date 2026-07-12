import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import AnonymousSessionRequest, AnonymousSessionResponse, TokenPair
from app.auth.security import hash_refresh_token, issue_access_token, new_refresh_token
from app.config import Settings
from app.db.models import Account, Device, Session


class AuthenticationError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class AuthenticatedSession:
    account: Account
    device: Device
    session: Session


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def token_pair(session: Session, refresh_token: str, settings: Settings) -> TokenPair:
    return TokenPair(
        access_token=issue_access_token(
            account_id=session.account_id,
            device_id=session.device_id,
            session_id=session.id,
            settings=settings,
        ),
        refresh_token=refresh_token,
        expires_in=settings.access_token_ttl_seconds,
    )


async def create_anonymous_session(
    db: AsyncSession, payload: AnonymousSessionRequest, settings: Settings
) -> AnonymousSessionResponse:
    existing = await db.scalar(
        select(Device.id).where(Device.installation_id == payload.installation_id)
    )
    if existing is not None:
        raise AuthenticationError(
            "DEVICE_ALREADY_REGISTERED",
            "This installation is already registered; refresh its existing session.",
        )

    account = Account()
    device = Device(
        account=account,
        platform=payload.platform,
        installation_id=payload.installation_id,
        last_seen_at=utcnow(),
    )
    refresh_token = new_refresh_token()
    session = Session(
        account=account,
        device=device,
        refresh_token_hash=hash_refresh_token(
            refresh_token, settings.refresh_token_pepper.get_secret_value()
        ),
        expires_at=utcnow() + timedelta(seconds=settings.refresh_token_ttl_seconds),
    )
    db.add(account)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise AuthenticationError(
            "DEVICE_ALREADY_REGISTERED",
            "This installation is already registered; refresh its existing session.",
        ) from exc
    await db.refresh(session)
    pair = token_pair(session, refresh_token, settings)
    return AnonymousSessionResponse(
        **pair.model_dump(),
        account_id=account.id,
        device_id=device.id,
        session_id=session.id,
    )


async def rotate_refresh_token(db: AsyncSession, raw_token: str, settings: Settings) -> TokenPair:
    digest = hash_refresh_token(raw_token, settings.refresh_token_pepper.get_secret_value())
    current = await db.scalar(
        select(Session).where(Session.refresh_token_hash == digest).with_for_update()
    )
    if current is None:
        raise AuthenticationError("INVALID_REFRESH_TOKEN", "Refresh token is invalid.")

    now = utcnow()
    if current.revoked_at is not None:
        await db.execute(
            update(Session)
            .where(
                Session.refresh_family_id == current.refresh_family_id,
                Session.revoked_at.is_(None),
            )
            .values(revoked_at=now, revoke_reason="refresh_replay")
        )
        await db.commit()
        raise AuthenticationError(
            "REFRESH_REPLAY_DETECTED",
            "Refresh credential replay was detected; the credential family is revoked.",
        )
    if current.expires_at <= now:
        current.revoked_at = now
        current.revoke_reason = "expired"
        await db.commit()
        raise AuthenticationError("REFRESH_TOKEN_EXPIRED", "Refresh token has expired.")

    current.revoked_at = now
    current.revoke_reason = "rotated"
    replacement_token = new_refresh_token()
    replacement = Session(
        account_id=current.account_id,
        device_id=current.device_id,
        refresh_family_id=current.refresh_family_id,
        refresh_token_hash=hash_refresh_token(
            replacement_token, settings.refresh_token_pepper.get_secret_value()
        ),
        expires_at=now + timedelta(seconds=settings.refresh_token_ttl_seconds),
    )
    db.add(replacement)
    await db.commit()
    await db.refresh(replacement)
    return token_pair(replacement, replacement_token, settings)


async def authenticate_session(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    session_id: uuid.UUID,
) -> AuthenticatedSession:
    row = await db.execute(
        select(Account, Device, Session)
        .join(Device, Device.account_id == Account.id)
        .join(Session, Session.device_id == Device.id)
        .where(
            Account.id == account_id,
            Device.id == device_id,
            Session.id == session_id,
        )
    )
    result = row.one_or_none()
    if result is None:
        raise AuthenticationError("INVALID_ACCESS_TOKEN", "Access token is invalid.")
    account, device, session = result
    if account.status != "active" or session.revoked_at is not None:
        raise AuthenticationError("SESSION_REVOKED", "Session is no longer active.")
    return AuthenticatedSession(account=account, device=device, session=session)


async def revoke_session(db: AsyncSession, session: Session, reason: str) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        session.revoke_reason = reason
        await db.commit()


async def revoke_device_sessions(
    db: AsyncSession, *, account_id: uuid.UUID, device_id: uuid.UUID
) -> int:
    device = await db.scalar(
        select(Device).where(Device.id == device_id, Device.account_id == account_id)
    )
    if device is None:
        raise AuthenticationError("DEVICE_NOT_FOUND", "Device was not found.")
    result = await db.execute(
        update(Session)
        .where(
            Session.device_id == device_id,
            Session.revoked_at.is_(None),
        )
        .values(revoked_at=utcnow(), revoke_reason="device_revoked")
    )
    await db.commit()
    return cast(int, cast(Any, result).rowcount or 0)
