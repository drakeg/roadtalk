import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.credentials import RegisteredCredential
from app.auth.passwords import (
    DUMMY_PASSWORD_HASH,
    hash_password,
    normalize_username,
    verify_password,
)
from app.auth.schemas import (
    AnonymousSessionRequest,
    AnonymousSessionResponse,
    RegisteredAuthRequest,
    RegisteredPromotionRequest,
    RegisteredSessionResponse,
    TokenPair,
)
from app.auth.security import hash_refresh_token, issue_access_token, new_refresh_token
from app.channels.constants import GENERAL_CHANNEL_ID
from app.config import Settings
from app.db.models import Account, ChannelSelection, Device, Session
from app.ptt.service import revoke_device_media_grants


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


def registered_response(
    session: Session,
    refresh_token: str,
    settings: Settings,
) -> RegisteredSessionResponse:
    pair = token_pair(session, refresh_token, settings)
    return RegisteredSessionResponse(
        **pair.model_dump(),
        account_id=session.account_id,
        device_id=session.device_id,
        session_id=session.id,
    )


async def _new_session_for_device(
    db: AsyncSession,
    *,
    account: Account,
    device: Device,
    settings: Settings,
) -> tuple[Session, str]:
    refresh_token = new_refresh_token()
    session = Session(
        account=account,
        device=device,
        refresh_token_hash=hash_refresh_token(
            refresh_token, settings.refresh_token_pepper.get_secret_value()
        ),
        expires_at=utcnow() + timedelta(seconds=settings.refresh_token_ttl_seconds),
    )
    db.add(session)
    return session, refresh_token


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
    session, refresh_token = await _new_session_for_device(
        db, account=account, device=device, settings=settings
    )
    account.channel_selection = ChannelSelection(channel_id=GENERAL_CHANNEL_ID)
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


async def create_registered_account(
    db: AsyncSession,
    payload: RegisteredAuthRequest,
    settings: Settings,
) -> RegisteredSessionResponse:
    try:
        username = normalize_username(payload.username)
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise AuthenticationError("INVALID_REGISTRATION", str(exc)) from exc

    if (
        await db.scalar(
            select(RegisteredCredential.account_id).where(
                RegisteredCredential.normalized_username == username
            )
        )
        is not None
    ):
        raise AuthenticationError("USERNAME_UNAVAILABLE", "That username is unavailable.")
    if (
        await db.scalar(select(Device.id).where(Device.installation_id == payload.installation_id))
        is not None
    ):
        raise AuthenticationError(
            "DEVICE_ALREADY_REGISTERED",
            "This installation is already attached to an account.",
        )

    account = Account(id=uuid.uuid4(), account_type="registered")
    account.channel_selection = ChannelSelection(channel_id=GENERAL_CHANNEL_ID)
    device = Device(
        account=account,
        platform=payload.platform,
        installation_id=payload.installation_id,
        last_seen_at=utcnow(),
    )
    credential = RegisteredCredential(
        account_id=account.id,
        normalized_username=username,
        password_hash=password_hash,
    )
    session, refresh_token = await _new_session_for_device(
        db, account=account, device=device, settings=settings
    )
    db.add_all((account, credential))
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise AuthenticationError(
            "REGISTRATION_CONFLICT", "Registration could not be completed."
        ) from exc
    await db.refresh(session)
    return registered_response(session, refresh_token, settings)


async def promote_registered_account(
    db: AsyncSession,
    *,
    current: AuthenticatedSession,
    payload: RegisteredPromotionRequest,
) -> None:
    try:
        username = normalize_username(payload.username)
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise AuthenticationError("INVALID_REGISTRATION", str(exc)) from exc

    if current.account.account_type == "registered":
        raise AuthenticationError("ALREADY_REGISTERED", "This account is already registered.")
    if (
        await db.scalar(
            select(RegisteredCredential.account_id).where(
                RegisteredCredential.normalized_username == username
            )
        )
        is not None
    ):
        raise AuthenticationError("USERNAME_UNAVAILABLE", "That username is unavailable.")

    current.account.account_type = "registered"
    db.add(
        RegisteredCredential(
            account_id=current.account.id,
            normalized_username=username,
            password_hash=password_hash,
        )
    )
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise AuthenticationError(
            "REGISTRATION_CONFLICT", "Registration could not be completed."
        ) from exc


async def login_registered_account(
    db: AsyncSession,
    payload: RegisteredAuthRequest,
    settings: Settings,
) -> RegisteredSessionResponse:
    try:
        username = normalize_username(payload.username)
    except ValueError:
        username = "invalid"

    credential = await db.scalar(
        select(RegisteredCredential).where(RegisteredCredential.normalized_username == username)
    )
    encoded = credential.password_hash if credential is not None else DUMMY_PASSWORD_HASH
    valid = verify_password(payload.password, encoded)
    if credential is None or not valid:
        raise AuthenticationError("INVALID_LOGIN", "Username or password is invalid.")

    account = await db.get(Account, credential.account_id)
    if account is None or account.status != "active" or account.account_type != "registered":
        raise AuthenticationError("INVALID_LOGIN", "Username or password is invalid.")

    device = await db.scalar(
        select(Device).where(Device.installation_id == payload.installation_id)
    )
    if device is not None and device.account_id != account.id:
        raise AuthenticationError(
            "DEVICE_ALREADY_REGISTERED",
            "This browser installation is attached to another account.",
        )
    if device is None:
        device = Device(
            account=account,
            platform=payload.platform,
            installation_id=payload.installation_id,
            last_seen_at=utcnow(),
        )
    else:
        device.last_seen_at = utcnow()

    session, refresh_token = await _new_session_for_device(
        db, account=account, device=device, settings=settings
    )
    db.add(device)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise AuthenticationError("LOGIN_CONFLICT", "Login could not be completed.") from exc
    await db.refresh(session)
    return registered_response(session, refresh_token, settings)


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
    settings: Settings,
    *,
    on_change: Callable[[AsyncSession, uuid.UUID], Awaitable[None]] | None = None,
) -> TokenPair:
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
        await revoke_device_media_grants(
            db,
            account_id=current.account_id,
            device_id=current.device_id,
            reason="session_revoked",
            now=now,
        )
        await db.commit()
        if on_change is not None:
            await on_change(db, current.account_id)
        raise AuthenticationError(
            "REFRESH_REPLAY_DETECTED",
            "Refresh credential replay was detected; the credential family is revoked.",
        )
    if current.expires_at <= now:
        current.revoked_at = now
        current.revoke_reason = "expired"
        await revoke_device_media_grants(
            db,
            account_id=current.account_id,
            device_id=current.device_id,
            reason="session_revoked",
            now=now,
        )
        await db.commit()
        if on_change is not None:
            await on_change(db, current.account_id)
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


async def revoke_session(
    db: AsyncSession,
    session: Session,
    reason: str,
    *,
    on_change: Callable[[AsyncSession, uuid.UUID], Awaitable[None]] | None = None,
) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        session.revoke_reason = reason
        await revoke_device_media_grants(
            db,
            account_id=session.account_id,
            device_id=session.device_id,
            reason="session_revoked",
            now=session.revoked_at,
        )
        await db.commit()
        if on_change is not None:
            await on_change(db, session.account_id)


async def revoke_device_sessions(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    on_change: Callable[[AsyncSession, uuid.UUID], Awaitable[None]] | None = None,
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
    await revoke_device_media_grants(
        db,
        account_id=account_id,
        device_id=device_id,
        reason="device_revoked",
    )
    await db.commit()
    if on_change is not None:
        await on_change(db, account_id)
    return cast(int, cast(Any, result).rowcount or 0)
