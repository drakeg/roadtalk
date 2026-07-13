import asyncio
import os

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, Profile
from app.identity.service import callsign_availability


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_normalized_callsign_uniqueness_and_owner_availability() -> None:
    asyncio.run(_callsign_lifecycle())


async def _callsign_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    first = Account()
    second = Account()

    try:
        async with factory() as db:
            db.add_all([first, second])
            await db.commit()

            db.add(
                Profile(
                    account_id=first.id,
                    normalized_callsign="road-runner",
                    display_callsign="Road-Runner",
                )
            )
            await db.commit()

            own = await callsign_availability(
                db,
                account_id=first.id,
                candidate="ROAD-RUNNER",
            )
            taken = await callsign_availability(
                db,
                account_id=second.id,
                candidate="road-runner",
            )
            assert own.available
            assert taken.model_dump() == {"available": False, "reason": "taken"}

            db.add(
                Profile(
                    account_id=second.id,
                    normalized_callsign="road-runner",
                    display_callsign="road-runner",
                )
            )
            with pytest.raises(IntegrityError):
                await db.commit()
            await db.rollback()

            await db.delete(first)
            await db.delete(second)
            await db.commit()
    finally:
        await engine.dispose()
