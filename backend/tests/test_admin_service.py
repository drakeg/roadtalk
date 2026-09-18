import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.admin.service import (
    AdminAuthorizationError,
    AdminMutationError,
    list_accounts,
    require_admin,
    revoke_account_sessions,
    set_account_enabled,
)
from app.auth.service import AuthenticatedSession, utcnow
from app.db.models import Account, AdminAuditEvent, Device, Profile, Session


def _current(account: Account, device: Device, session: Session) -> AuthenticatedSession:
    return AuthenticatedSession(account=account, device=device, session=session)


def test_normal_account_fails_closed() -> None:
    account = Account(id=uuid.uuid4(), is_admin=False)
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="ios",
        installation_id="admin-test-normal",
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


@pytest.mark.asyncio
async def test_admin_account_listing_is_support_safe(db_session) -> None:
    admin = Account(id=uuid.uuid4(), account_type="registered", is_admin=True)
    admin_device = Device(
        id=uuid.uuid4(),
        account=admin,
        platform="ios",
        installation_id="admin-test-admin",
    )
    admin_session = Session(
        id=uuid.uuid4(),
        account=admin,
        device=admin_device,
        refresh_token_hash="admin-session",
        expires_at=utcnow() + timedelta(hours=1),
    )
    target = Account(id=uuid.uuid4(), account_type="registered")
    target.profile = Profile(
        normalized_callsign="traveler",
        display_callsign="Traveler",
        avatar_id="default-web",
        setup_completed=True,
        callsign_changed_at=utcnow(),
    )
    db_session.add_all([admin, target])
    await db_session.commit()

    require_admin(_current(admin, admin_device, admin_session))
    response = await list_accounts(db_session, query="Traveler")
    assert len(response.accounts) == 1
    payload = response.model_dump()
    assert payload["accounts"][0]["callsign"] == "Traveler"
    serialized = str(payload).lower()
    for forbidden in ("password", "recovery", "location", "media_secret", "refresh_token"):
        assert forbidden not in serialized


@pytest.mark.asyncio
async def test_disable_requires_confirmation_and_revokes_sessions(db_session) -> None:
    admin = Account(id=uuid.uuid4(), account_type="registered", is_admin=True)
    admin_device = Device(
        id=uuid.uuid4(),
        account=admin,
        platform="ios",
        installation_id="admin-test-mutator",
    )
    admin_session = Session(
        id=uuid.uuid4(),
        account=admin,
        device=admin_device,
        refresh_token_hash="admin-mutator-session",
        expires_at=utcnow() + timedelta(hours=1),
    )
    target = Account(id=uuid.uuid4(), account_type="registered")
    target_device = Device(
        id=uuid.uuid4(),
        account=target,
        platform="ios",
        installation_id="admin-test-target",
    )
    target_session = Session(
        id=uuid.uuid4(),
        account=target,
        device=target_device,
        refresh_token_hash="target-session",
        expires_at=utcnow() + timedelta(hours=1),
    )
    db_session.add_all([admin, target])
    await db_session.commit()

    with pytest.raises(AdminMutationError):
        await set_account_enabled(
            db_session,
            actor=_current(admin, admin_device, admin_session),
            target_account_id=target.id,
            enabled=False,
            confirmed=False,
        )

    result = await set_account_enabled(
        db_session,
        actor=_current(admin, admin_device, admin_session),
        target_account_id=target.id,
        enabled=False,
        confirmed=True,
    )
    await db_session.refresh(target_session)
    assert result.status == "disabled"
    assert target_session.revoked_at is not None
    audit = await db_session.scalar(
        select(AdminAuditEvent).where(AdminAuditEvent.target_account_id == target.id)
    )
    assert audit is not None
    assert audit.action == "account_disabled"


@pytest.mark.asyncio
async def test_session_revocation_is_confirmed_and_audited(db_session) -> None:
    admin = Account(id=uuid.uuid4(), account_type="registered", is_admin=True)
    admin_device = Device(
        id=uuid.uuid4(),
        account=admin,
        platform="ios",
        installation_id="admin-test-revoker",
    )
    admin_session = Session(
        id=uuid.uuid4(),
        account=admin,
        device=admin_device,
        refresh_token_hash="admin-revoker-session",
        expires_at=utcnow() + timedelta(hours=1),
    )
    target = Account(id=uuid.uuid4(), account_type="registered")
    target_device = Device(
        id=uuid.uuid4(),
        account=target,
        platform="ios",
        installation_id="admin-test-revoke-target",
    )
    target_session = Session(
        id=uuid.uuid4(),
        account=target,
        device=target_device,
        refresh_token_hash="target-revoke-session",
        expires_at=utcnow() + timedelta(hours=1),
    )
    db_session.add_all([admin, target])
    await db_session.commit()

    result = await revoke_account_sessions(
        db_session,
        actor=_current(admin, admin_device, admin_session),
        target_account_id=target.id,
        confirmed=True,
    )
    assert result.revoked_sessions == 1
    audit = await db_session.scalar(
        select(AdminAuditEvent).where(
            AdminAuditEvent.target_account_id == target.id,
            AdminAuditEvent.action == "sessions_revoked",
        )
    )
    assert audit is not None
