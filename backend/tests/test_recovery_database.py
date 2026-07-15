import asyncio
import os

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.schemas import AnonymousSessionRequest
from app.auth.service import (
    AuthenticationError,
    authenticate_session,
    create_anonymous_session,
)
from app.config import Settings
from app.db.models import Account, RecoveryCredential
from app.recovery.service import (
    RecoveryError,
    create_or_rotate_recovery_key,
    recover_account,
)


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_recovery_transfer_rotation_replay_and_revocation() -> None:
    asyncio.run(_recovery_lifecycle())


async def _recovery_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    suffix = os.urandom(16).hex()

    try:
        async with factory() as db:
            original = await create_anonymous_session(
                db,
                AnonymousSessionRequest(
                    installation_id=f"original-{suffix}",
                    platform="ios",
                ),
                settings,
            )
            issued = await create_or_rotate_recovery_key(
                db,
                account_id=original.account_id,
                settings=settings,
            )
            temporary = await create_anonymous_session(
                db,
                AnonymousSessionRequest(
                    installation_id=f"replacement-{suffix}",
                    platform="ios",
                ),
                settings,
            )

            recovered = await recover_account(
                db,
                raw_key=issued.recovery_key,
                installation_id=f"replacement-{suffix}",
                platform="ios",
                settings=settings,
            )

            assert recovered.account_id == original.account_id
            assert recovered.device_id == temporary.device_id
            assert recovered.recovery_key != issued.recovery_key
            temporary_account = await db.scalar(
                select(Account.id).where(Account.id == temporary.account_id)
            )
            assert temporary_account is None

            for session in (original, temporary):
                with pytest.raises(AuthenticationError):
                    await authenticate_session(
                        db,
                        account_id=session.account_id,
                        device_id=session.device_id,
                        session_id=session.session_id,
                    )

            active = await authenticate_session(
                db,
                account_id=recovered.account_id,
                device_id=recovered.device_id,
                session_id=recovered.session_id,
            )
            assert active.account.id == original.account_id

            with pytest.raises(RecoveryError) as replay:
                await recover_account(
                    db,
                    raw_key=issued.recovery_key,
                    installation_id=f"replay-{suffix}",
                    platform="android",
                    settings=settings,
                )
            assert replay.value.code == "RECOVERY_FAILED"

            second_recovery = await recover_account(
                db,
                raw_key=recovered.recovery_key,
                installation_id=f"third-{suffix}",
                platform="android",
                settings=settings,
            )
            assert second_recovery.account_id == original.account_id
            assert second_recovery.recovery_key != recovered.recovery_key

            credential = await db.scalar(
                select(RecoveryCredential).where(
                    RecoveryCredential.account_id == original.account_id
                )
            )
            assert credential is not None
            assert issued.recovery_key not in credential.key_hash
            assert recovered.recovery_key not in credential.key_hash

            await db.execute(delete(Account).where(Account.id == original.account_id))
            await db.commit()
    finally:
        await engine.dispose()
