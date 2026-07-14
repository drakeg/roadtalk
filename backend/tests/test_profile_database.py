import asyncio
import os

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account
from app.identity.service import ProfileMutationError, read_profile, update_profile


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_owner_profile_conditional_update_lifecycle() -> None:
    asyncio.run(_profile_lifecycle())


async def _profile_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    first = Account()
    second = Account()

    try:
        async with factory() as db:
            db.add_all([first, second])
            await db.commit()
            first_id = first.id
            second_id = second.id

            missing = await read_profile(db, account_id=first_id)
            assert missing.version == 0

            created = await update_profile(
                db,
                account_id=first_id,
                candidate="Road-Runner",
                expected_version=0,
                cooldown_seconds=0,
            )
            assert created.version == 1
            assert created.identity.callsign == "Road-Runner"

            updated = await update_profile(
                db,
                account_id=first_id,
                candidate="Night-Owl",
                expected_version=1,
                cooldown_seconds=0,
            )
            assert updated.version == 2

            with pytest.raises(ProfileMutationError) as stale:
                await update_profile(
                    db,
                    account_id=first_id,
                    candidate="Road-Ranger",
                    expected_version=1,
                    cooldown_seconds=0,
                )
            assert stale.value.code == "PROFILE_VERSION_CONFLICT"

            with pytest.raises(ProfileMutationError) as collision:
                await update_profile(
                    db,
                    account_id=second_id,
                    candidate="NIGHT-OWL",
                    expected_version=0,
                    cooldown_seconds=0,
                )
            assert collision.value.code == "CALLSIGN_UNAVAILABLE"

            first_read = await read_profile(db, account_id=first_id)
            second_read = await read_profile(db, account_id=second_id)
            assert first_read.identity.callsign == "Night-Owl"
            assert second_read.version == 0

            await db.execute(delete(Account).where(Account.id.in_([first_id, second_id])))
            await db.commit()
    finally:
        await engine.dispose()
