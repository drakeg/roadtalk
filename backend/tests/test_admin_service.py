import asyncio
import os
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.admin.service import (
    AdminAuthorizationError,
    AdminMutationError,
    list_accounts,
    require_admin,
    revoke_account_sessions,
    set_account_enabled,
)
from app.auth.service import AuthenticatedSession, utcnow
from app.config import Settings
from app.db.models import Account, AdminAuditEvent, Device, Profile, Session


def _current(account: Account, device: Device, session: Session) -> AuthenticatedSession:
    return AuthenticatedSession(account=account, device=device, session=session)


def test_normal_account_fails_closed() -> None:
    account = Account(id=uuid.uuid4(), is_admin=False)
    device = Device(
        id=uuid.uuid4(), account=account, platform="ios", installation_id="admin-normal"
    )
    session = Session(
        id=uuid.uuid4(),
        account=account,
        device=device,
        refresh_token_hash="normal-session",
        expires_at=utcnow() + timedelta(hours=1),
    )
    with pytest.raises(AdminAuthorizationError):
        require_admin(_current(account, device, session))


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_admin_database_contract() -> None:
    asyncio.run(_admin_database_contract())


async def _admin_database_contract() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    suffix = os.urandom(8).hex()
    try:
        async with factory() as db:
            admin = Account(id=uuid.uuid4(), account_type="registered", is_admin=True)
            admin_device = Device(
                id=uuid.uuid4(),
                account=admin,
                platform="ios",
                installation_id=f"admin-{suffix}",
            )
            admin_session = Session(
                id=uuid.uuid4(),
                account=admin,
                device=admin_device,
                refresh_token_hash=f"admin-session-{suffix}",
                expires_at=utcnow() + timedelta(hours=1),
            )
            target = Account(id=uuid.uuid4(), account_type="registered")
            target.profile = Profile(
                normalized_callsign=f"traveler-{suffix}",
                display_callsign=f"Traveler-{suffix}",
                avatar_id="default-web",
                setup_completed=True,
                callsign_changed_at=utcnow(),
            )
            target_device = Device(
                id=uuid.uuid4(),
                account=target,
                platform="ios",
                installation_id=f"target-{suffix}",
            )
            target_session = Session(
                id=uuid.uuid4(),
                account=target,
                device=target_device,
                refresh_token_hash=f"target-session-{suffix}",
                expires_at=utcnow() + timedelta(hours=1),
            )
            db.add_all([admin, target])
            await db.commit()

            require_admin(_current(admin, admin_device, admin_session))
            listing = await list_accounts(db, query=f"Traveler-{suffix}")
            assert len(listing.accounts) == 1
            serialized = str(listing.model_dump()).lower()
            for forbidden in ("password", "recovery", "location", "media_secret", "refresh_token"):
                assert forbidden not in serialized

            with pytest.raises(AdminMutationError):
                await set_account_enabled(
                    db,
                    actor=_current(admin, admin_device, admin_session),
                    target_account_id=target.id,
                    enabled=False,
                    confirmed=False,
                )
            result = await set_account_enabled(
                db,
                actor=_current(admin, admin_device, admin_session),
                target_account_id=target.id,
                enabled=False,
                confirmed=True,
            )
            await db.refresh(target_session)
            assert result.status == "disabled"
            assert target_session.revoked_at is not None
            audit = await db.scalar(
                select(AdminAuditEvent).where(AdminAuditEvent.target_account_id == target.id)
            )
            assert audit is not None
            assert audit.action == "account_disabled"

            await set_account_enabled(
                db,
                actor=_current(admin, admin_device, admin_session),
                target_account_id=target.id,
                enabled=True,
                confirmed=True,
            )
            fresh_session = Session(
                account=target,
                device=target_device,
                refresh_token_hash=f"fresh-target-session-{suffix}",
                expires_at=utcnow() + timedelta(hours=1),
            )
            db.add(fresh_session)
            await db.commit()
            revoked = await revoke_account_sessions(
                db,
                actor=_current(admin, admin_device, admin_session),
                target_account_id=target.id,
                confirmed=True,
            )
            assert revoked.revoked_sessions >= 1
    finally:
        await engine.dispose()
