import asyncio
import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, Device, MediaGrant
from app.ptt.provider import FakeMediaProvider, MediaProviderError, MicrophonePublishRequest
from app.ptt.service import (
    GrantError,
    create_receive_grant,
    create_transmit_grant,
    release_receive_grant,
    release_transmit_grant,
)


class FailingPublishProvider(FakeMediaProvider):
    async def set_microphone_publish(self, request: MicrophonePublishRequest) -> None:
        self.publish_requests.append(request)
        if request.enabled:
            raise MediaProviderError("synthetic ambiguous provider failure")


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
            account_id = account.id

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

            transmit = await create_transmit_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                receive_grant_id=created.grant_id,
                idempotency_key="database-transmit-key-0001",
                settings=settings,
                provider=provider,
                now=now,
            )
            transmit_replay = await create_transmit_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                receive_grant_id=created.grant_id,
                idempotency_key="database-transmit-key-0001",
                settings=settings,
                provider=provider,
                now=now,
            )
            assert transmit.replayed is False
            assert transmit_replay.grant_id == transmit.grant_id
            assert transmit_replay.replayed is True
            assert sum(request.enabled for request in provider.publish_requests) == 1

            with pytest.raises(GrantError) as busy:
                await create_transmit_grant(
                    db,
                    account_id=account.id,
                    device_id=device.id,
                    receive_grant_id=created.grant_id,
                    idempotency_key="database-transmit-key-0002",
                    settings=settings,
                    provider=provider,
                    now=now,
                )
            assert busy.value.code == "PTT_TRANSMIT_BUSY"

            transmit_release = await release_transmit_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                grant_id=transmit.grant_id,
                provider=provider,
                now=now,
            )
            transmit_release_replay = await release_transmit_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                grant_id=transmit.grant_id,
                provider=provider,
                now=now,
            )
            assert transmit_release.replayed is False
            assert transmit_release_replay.replayed is True
            assert provider.publish_requests[-1].enabled is False

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

            cleanup_receive = await create_receive_grant(
                db,
                account_id=account.id,
                device_id=device.id,
                idempotency_key="database-key-cleanup",
                settings=settings,
                provider=provider,
                now=now,
                random_ref=lambda: "opaque-cleanup",
            )
            failing_provider = FailingPublishProvider(now=lambda: now)
            with pytest.raises(GrantError) as provider_failure:
                await create_transmit_grant(
                    db,
                    account_id=account.id,
                    device_id=device.id,
                    receive_grant_id=cleanup_receive.grant_id,
                    idempotency_key="database-transmit-key-failure",
                    settings=settings,
                    provider=failing_provider,
                    now=now,
                )
            assert provider_failure.value.code == "PTT_PROVIDER_UNAVAILABLE"
            assert [request.enabled for request in failing_provider.publish_requests] == [
                True,
                False,
            ]
            assert len(failing_provider.remove_requests) == 1
            cleanup_stored = await db.scalar(
                select(MediaGrant).where(MediaGrant.id == cleanup_receive.grant_id)
            )
            assert cleanup_stored is not None
            assert cleanup_stored.revoked_at == now
            assert cleanup_stored.outcome_code == "provider_cleanup_pending"
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(MediaGrant)
                    .where(
                        MediaGrant.account_id == account_id,
                        MediaGrant.grant_kind == "transmit",
                    )
                )
                == 1
            )

            stored = await db.scalar(select(MediaGrant).where(MediaGrant.id == created.grant_id))
            assert stored is not None
            assert stored.idempotency_key_hash != "database-key-0001"
            assert len(stored.idempotency_key_hash) == 64
            assert not any(
                fragment in column.name
                for column in MediaGrant.__table__.c
                for fragment in ("token", "secret", "audio", "transcript", "listener")
            )

            await db.execute(delete(Account).where(Account.id == account_id))
            await db.commit()
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(MediaGrant)
                    .where(MediaGrant.account_id == account_id)
                )
                == 0
            )
    finally:
        await engine.dispose()
