import asyncio
import os
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Account, Device, MediaGrant
from app.ptt.provider import (
    FakeMediaProvider,
    MediaProviderError,
    MicrophonePublishRequest,
    ProviderTrackState,
)
from app.ptt.proximity import EligibleReceiveGrant, ProximityPolicy
from app.ptt.service import (
    GrantError,
    create_receive_grant,
    create_transmit_grant,
    publish_transmit_track,
    release_receive_grant,
    release_transmit_grant,
)


async def _synthetic_eligible_audience(
    db: AsyncSession,
    *,
    sender_account_id: uuid.UUID,
    sender_device_id: uuid.UUID,
    policy: ProximityPolicy,
    now: datetime | None = None,
) -> tuple[EligibleReceiveGrant, ...]:
    del db, sender_account_id, sender_device_id, policy, now
    return (
        EligibleReceiveGrant(
            receive_grant_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
            participant_ref="participant_synthetic_eligible",
        ),
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
                eligibility_finder=_synthetic_eligible_audience,
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

            publication_provider = FakeMediaProvider(
                now=lambda: now,
                tracks=(
                    ProviderTrackState(
                        room_ref=settings.ptt_controlled_room_ref,
                        participant_ref=created.participant_ref,
                        track_ref="database_microphone_track_opaque",
                        source="microphone",
                        active=True,
                    ),
                ),
            )
            publication = await publish_transmit_track(
                db,
                account_id=account.id,
                device_id=device.id,
                transmit_grant_id=transmit.grant_id,
                track_ref="database_microphone_track_opaque",
                settings=settings,
                provider=publication_provider,
                eligibility_finder=_synthetic_eligible_audience,
                now=now,
            )
            publication_replay = await publish_transmit_track(
                db,
                account_id=account.id,
                device_id=device.id,
                transmit_grant_id=transmit.grant_id,
                track_ref="database_microphone_track_opaque",
                settings=settings,
                provider=publication_provider,
                now=now,
            )
            assert publication.delivery_state == "ready"
            assert publication_replay.replayed is True
            assert len(publication_provider.track_lookup_requests) == 1
            assert len(publication_provider.subscription_requests) == 1
            stored_publication = await db.scalar(
                select(MediaGrant).where(MediaGrant.id == transmit.grant_id)
            )
            assert stored_publication is not None
            assert stored_publication.provider_track_ref == "database_microphone_track_opaque"
            assert stored_publication.proximity_policy_version == "proximity-v1"
            assert stored_publication.eligibility_evaluated_at == now
            assert stored_publication.outcome_code == "delivery_ready"

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
                    eligibility_finder=_synthetic_eligible_audience,
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
