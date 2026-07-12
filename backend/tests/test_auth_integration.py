import asyncio
import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.schemas import AnonymousSessionRequest
from app.auth.service import (
    AuthenticationError,
    authenticate_session,
    create_anonymous_session,
    revoke_device_sessions,
    rotate_refresh_token,
)
from app.config import Settings


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_anonymous_session_rotation_replay_and_device_revocation() -> None:
    asyncio.run(_lifecycle())


async def _lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    installation_id = "integration-" + os.urandom(16).hex()

    try:
        async with factory() as db:
            created = await create_anonymous_session(
                db,
                AnonymousSessionRequest(
                    installation_id=installation_id,
                    platform="ios",
                ),
                settings,
            )
            identity = await authenticate_session(
                db,
                account_id=created.account_id,
                device_id=created.device_id,
                session_id=created.session_id,
            )
            assert identity.account.account_type == "anonymous"

            replacement = await rotate_refresh_token(
                db, created.refresh_token, settings
            )
            with pytest.raises(AuthenticationError) as replay:
                await rotate_refresh_token(db, created.refresh_token, settings)
            assert replay.value.code == "REFRESH_REPLAY_DETECTED"

            with pytest.raises(AuthenticationError) as family_revoked:
                await rotate_refresh_token(db, replacement.refresh_token, settings)
            assert family_revoked.value.code == "REFRESH_REPLAY_DETECTED"

            count = await revoke_device_sessions(
                db,
                account_id=created.account_id,
                device_id=created.device_id,
            )
            assert count == 0
            await db.delete(identity.account)
            await db.commit()
    finally:
        await engine.dispose()
