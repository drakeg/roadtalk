import asyncio
import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.credentials import RegisteredCredential
from app.auth.schemas import (
    AnonymousSessionRequest,
    RegisteredAuthRequest,
    RegisteredPromotionRequest,
)
from app.auth.service import (
    authenticate_session,
    create_anonymous_session,
    create_registered_account,
    login_registered_account,
    promote_registered_account,
)
from app.config import Settings
from app.db.models import Account, Profile


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_registered_login_restores_same_account_and_callsign() -> None:
    asyncio.run(_registered_lifecycle())


async def _registered_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    suffix = os.urandom(8).hex()
    username = f"roadtalk-{suffix}"
    password = "correct horse battery staple"
    first_install = "registered-first-" + os.urandom(16).hex()
    second_install = "registered-second-" + os.urandom(16).hex()

    try:
        async with factory() as db:
            created = await create_registered_account(
                db,
                RegisteredAuthRequest(
                    username=username,
                    password=password,
                    installation_id=first_install,
                    platform="web",
                ),
                settings,
            )
            profile = Profile(
                account_id=created.account_id,
                normalized_callsign=f"driver-{suffix}",
                display_callsign=f"Driver-{suffix}",
                avatar_id="duck-01",
                setup_completed=True,
            )
            db.add(profile)
            await db.commit()

            logged_in = await login_registered_account(
                db,
                RegisteredAuthRequest(
                    username=username,
                    password=password,
                    installation_id=second_install,
                    platform="web",
                ),
                settings,
            )
            assert logged_in.account_id == created.account_id
            restored = await db.get(Profile, logged_in.account_id)
            assert restored is not None
            assert restored.display_callsign == f"Driver-{suffix}"
            restored_account = await db.get(Account, logged_in.account_id)
            assert restored_account is not None
            assert restored_account.account_type == "registered"

            account = await db.get(Account, created.account_id)
            assert account is not None
            await db.delete(account)
            await db.commit()
    finally:
        await engine.dispose()


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_promoting_anonymous_account_preserves_profile_and_account_id() -> None:
    asyncio.run(_promotion_lifecycle())


async def _promotion_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    suffix = os.urandom(8).hex()
    install = "promotion-" + os.urandom(16).hex()
    username = f"promote-{suffix}"
    password = "persistent roadtalk account password"

    try:
        async with factory() as db:
            created = await create_anonymous_session(
                db,
                AnonymousSessionRequest(installation_id=install, platform="web"),
                settings,
            )
            db.add(
                Profile(
                    account_id=created.account_id,
                    normalized_callsign=f"owner-{suffix}",
                    display_callsign=f"Owner-{suffix}",
                    avatar_id="duck-01",
                    setup_completed=True,
                )
            )
            await db.commit()
            current = await authenticate_session(
                db,
                account_id=created.account_id,
                device_id=created.device_id,
                session_id=created.session_id,
            )

            await promote_registered_account(
                db,
                current=current,
                payload=RegisteredPromotionRequest(username=username, password=password),
            )
            account = await db.get(Account, created.account_id)
            profile = await db.get(Profile, created.account_id)
            credential = await db.get(RegisteredCredential, created.account_id)
            assert account is not None
            assert account.account_type == "registered"
            assert profile is not None
            assert profile.display_callsign == f"Owner-{suffix}"
            assert credential is not None

            logged_in = await login_registered_account(
                db,
                RegisteredAuthRequest(
                    username=username,
                    password=password,
                    installation_id=install,
                    platform="web",
                ),
                settings,
            )
            assert logged_in.account_id == created.account_id

            await db.delete(account)
            await db.commit()
    finally:
        await engine.dispose()
