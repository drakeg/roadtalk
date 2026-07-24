import asyncio
import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, Device, MediaGrant
from app.ptt.provider import FakeMediaProvider
from app.ptt.service import GrantError, create_receive_grant, release_receive_grant


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_receive_grant_is_idempotent_metadata_only_and_releasable() -> None:
    asyncio.run(_receive_grant_lifecycle())


async def _receive_grant_lifecycle() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime(2026, 7, 24, 1, tzinfo=UTC)
    account = Account()
    device = Device(
        account=account,
        platform="ios",
        installation_id=f"ptt-grant-{datetime.now(UTC).timestamp()}",
    )
    other_device = Device(
        account=account,
        platform="android",
        installation_id=f"ptt-grant-other-{datetime.now(UTC).timestamp()}",
    )
    provider = FakeMediaProvider(now=lambda: now)

    try:
        async with factory() as db:
            db.add_all([account, device, other_device])
            await db.commit()

            created = await create_receive_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                idempotency_key="database-key-0001",
                settings=settings,
                provider=provider,
                now=now,
                random_ref=lambda: "opaque0001",
            )
            replayed = await create_receive_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                idempotency_key="database-key-0001",
                settings=settings,
                provider=provider,
                now=now,
                random_ref=lambda: "must-not-be-used",
            )

            assert created.replayed is False
            assert created.participant_token is not None
            assert replayed.grant_id == created.grant_id
            assert replayed.replayed is True
            assert replayed.participant_token is None
            assert len(provider.receive_requests) == 1
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(MediaGrant)
                    .where(MediaGrant.account_id == account.id)
                )
                == 1
            )

            with pytest.raises(GrantError) as cross_device_replay:
                await create_receive_grant(
                    db,
                    account_id=account.id,
                    device_id=other_device.id,
                    idempotency_key="database-key-0001",
                    settings=settings,
                    provider=provider,
                    now=now,
                )
            assert cross_device_replay.value.code == "PTT_IDEMPOTENCY_CONFLICT"

            with pytest.raises(GrantError) as cross_device_release:
                await release_receive_grant(
                    db,
                    account_id=account.id,
                    device_id=other_device.id,
                    grant_id=created.grant_id,
                    provider=provider,
                    now=now,
                )
            assert cross_device_release.value.code == "PTT_GRANT_NOT_FOUND"

            with pytest.raises(GrantError) as active:
                await create_receive_grant(
                    db,
                    account_id=account.id,
                    device_id=device.id,
                    idempotency_key="database-key-0002",
                    settings=settings,
                    provider=provider,
                    now=now,
                )
            assert active.value.code == "PTT_RECEIVE_ALREADY_ACTIVE"

            released = await release_receive_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                grant_id=created.grant_id,
                provider=provider,
                now=now,
            )
            release_replay = await release_receive_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                grant_id=created.grant_id,
                provider=provider,
                now=now,
            )
            assert released.replayed is False
            assert release_replay.replayed is True
            assert len(provider.remove_requests) == 1

            stored = await db.scalar(select(MediaGrant).where(MediaGrant.id == created.grant_id))
            assert stored is not None
            assert stored.idempotency_key_hash != "database-key-0001"
            assert len(stored.idempotency_key_hash) == 64
            assert not any(
                fragment in column.name
                for column in MediaGrant.__table__.c
                for fragment in ("token", "secret", "audio", "transcript", "listener")
            )

            await db.execute(delete(Account).where(Account.id == account.id))
            await db.commit()
    finally:
        await engine.dispose()
