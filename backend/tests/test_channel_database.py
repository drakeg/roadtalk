import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.channels.constants import GENERAL_CHANNEL_ID, RV_CHANNEL_ID
from app.channels.service import (
    ChannelError,
    close_private_channel,
    create_private_channel,
    join_private_channel,
    leave_private_channel,
    list_channels,
    rotate_private_invite,
    select_channel,
)
from app.config import Settings
from app.db.models import (
    Account,
    Channel,
    ChannelInvite,
    ChannelMembership,
    ChannelSelection,
    Device,
    MediaGrant,
)
from app.ptt.provider import FakeMediaProvider
from app.ptt.service import create_receive_grant


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_channel_catalog_selection_concurrency_and_grant_binding() -> None:
    asyncio.run(_channel_catalog_selection())


@pytest.mark.skipif(
    os.getenv("ROADTALK_RUN_DATABASE_TESTS") != "1",
    reason="Set ROADTALK_RUN_DATABASE_TESTS=1 against a migrated disposable database.",
)
def test_private_channel_invite_lifecycle() -> None:
    asyncio.run(_private_channel_invite_lifecycle())


async def _private_channel_invite_lifecycle() -> None:
    settings = Settings(environment="test", channel_invite_pepper="test-channel-pepper")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner = Account(channel_selection=ChannelSelection(channel_id=GENERAL_CHANNEL_ID))
    member = Account(channel_selection=ChannelSelection(channel_id=GENERAL_CHANNEL_ID))
    owner_device = Device(account=owner, platform="ios", installation_id=f"owner-{uuid.uuid4()}")
    member_device = Device(
        account=member, platform="android", installation_id=f"member-{uuid.uuid4()}"
    )
    cleanup_account_ids: tuple[uuid.UUID, ...] = ()
    try:
        async with factory() as db:
            db.add_all([owner, member, owner_device, member_device])
            await db.commit()
            cleanup_account_ids = (owner.id, member.id)

            created = await create_private_channel(
                db,
                account_id=owner.id,
                display_label="  Camp   Friends  ",
                idempotency_key="create-private-database-0001",
                settings=settings,
            )
            assert created.display_label == "Camp Friends"
            assert created.invite is not None
            first_invite = created.invite
            create_replay = await create_private_channel(
                db,
                account_id=owner.id,
                display_label="Camp Friends",
                idempotency_key="create-private-database-0001",
                settings=settings,
            )
            assert create_replay.id == created.id
            assert create_replay.replayed is True
            assert create_replay.invite is None
            stored = await db.get(ChannelInvite, created.id)
            assert stored is not None
            assert first_invite not in stored.secret_hash
            assert len(stored.fingerprint) == 12

            joined = await join_private_channel(
                db, account_id=member.id, raw_invite=first_invite, settings=settings
            )
            replayed = await join_private_channel(
                db, account_id=member.id, raw_invite=first_invite, settings=settings
            )
            assert joined.replayed is False
            assert replayed.replayed is True

            rotated = await rotate_private_invite(
                db,
                account_id=owner.id,
                channel_id=created.id,
                idempotency_key="rotate-private-database-0001",
                settings=settings,
            )
            assert rotated.invite is not None and rotated.invite != first_invite
            rotation_replay = await rotate_private_invite(
                db,
                account_id=owner.id,
                channel_id=created.id,
                idempotency_key="rotate-private-database-0001",
                settings=settings,
            )
            assert rotation_replay.replayed is True
            assert rotation_replay.invite is None
            with pytest.raises(ChannelError) as old_invite:
                await join_private_channel(
                    db, account_id=uuid.uuid4(), raw_invite=first_invite, settings=settings
                )
            assert old_invite.value.code == "CHANNEL_INVITE_INVALID"

            now = datetime.now(UTC)
            await select_channel(db, account_id=owner.id, channel_id=created.id, now=now)
            await select_channel(db, account_id=member.id, channel_id=created.id, now=now)
            provider = FakeMediaProvider(now=lambda: now)
            owner_receive = await create_receive_grant(
                db,
                account_id=owner.id,
                device_id=owner_device.id,
                idempotency_key="owner-private-receive",
                settings=settings,
                provider=provider,
                now=now,
            )
            member_receive = await create_receive_grant(
                db,
                account_id=member.id,
                device_id=member_device.id,
                idempotency_key="member-private-receive",
                settings=settings,
                provider=provider,
                now=now,
            )

            left = await leave_private_channel(db, account_id=member.id, channel_id=created.id)
            left_replay = await leave_private_channel(
                db, account_id=member.id, channel_id=created.id
            )
            assert left.replayed is False
            assert left_replay.replayed is True
            stored_member_receive = await db.get(MediaGrant, member_receive.grant_id)
            assert stored_member_receive is not None
            await db.refresh(stored_member_receive)
            assert stored_member_receive.outcome_code == "channel_left"

            closed = await close_private_channel(db, account_id=owner.id, channel_id=created.id)
            closed_replay = await close_private_channel(
                db, account_id=owner.id, channel_id=created.id
            )
            assert closed.replayed is False
            assert closed_replay.replayed is True
            stored_owner_receive = await db.get(MediaGrant, owner_receive.grant_id)
            assert stored_owner_receive is not None
            await db.refresh(stored_owner_receive)
            assert stored_owner_receive.outcome_code == "channel_closed"
            assert (
                await db.scalar(
                    select(ChannelSelection.channel_id).where(
                        ChannelSelection.account_id == owner.id
                    )
                )
                == GENERAL_CHANNEL_ID
            )
    finally:
        async with factory() as db:
            await db.execute(
                delete(MediaGrant).where(MediaGrant.account_id.in_(cleanup_account_ids))
            )
            await db.commit()
            for account_id in cleanup_account_ids:
                stored_account = await db.get(Account, account_id)
                if stored_account is not None:
                    await db.delete(stored_account)
            await db.commit()
        await engine.dispose()


async def _channel_catalog_selection() -> None:
    settings = Settings(environment="test")
    engine = create_async_engine(settings.database_url.get_secret_value())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    marker = uuid.uuid4().hex
    account = Account()
    other_account = Account()
    account.channel_selection = ChannelSelection(channel_id=GENERAL_CHANNEL_ID)
    other_account.channel_selection = ChannelSelection(channel_id=GENERAL_CHANNEL_ID)
    device = Device(
        account=account,
        platform="ios",
        installation_id=f"channel-database-{marker}",
    )
    private = Channel(
        display_label="Private Alpha",
        channel_type="private",
        enabled=True,
        creator=account,
        provider_room_ref=f"rm_private_{marker}",
        policy_version="channel-v1",
        version=1,
    )
    other_private = Channel(
        display_label="Private Hidden",
        channel_type="private",
        enabled=True,
        creator=other_account,
        provider_room_ref=f"rm_hidden_{marker}",
        policy_version="channel-v1",
        version=1,
    )
    membership = ChannelMembership(account=account, channel=private)
    cleanup_account_ids: tuple[uuid.UUID, ...] = ()

    try:
        async with factory() as db:
            db.add_all([account, other_account, device, private, other_private, membership])
            await db.commit()
            account_id = account.id
            other_account_id = other_account.id
            cleanup_account_ids = (account_id, other_account_id)
            device_id = device.id
            private_id = private.id
            other_private_id = other_private.id

            public_channels = (
                await db.scalars(
                    select(Channel)
                    .where(Channel.channel_type == "public")
                    .order_by(Channel.stable_slug)
                )
            ).all()
            assert [
                (item.id, item.stable_slug, item.display_label) for item in public_channels
            ] == [
                (GENERAL_CHANNEL_ID, "general", "General"),
                (RV_CHANNEL_ID, "rv", "RV"),
            ]
            assert len({item.provider_room_ref for item in public_channels}) == 2
            assert all(item.creator_account_id is None for item in public_channels)

            catalog = await list_channels(db, account_id=account_id)
            assert [(item.slug, item.display_label) for item in catalog] == [
                ("general", "General"),
                ("rv", "RV"),
                (None, "Private Alpha"),
            ]
            assert sum(item.selected for item in catalog) == 1

            with pytest.raises(ChannelError) as hidden:
                await select_channel(
                    db,
                    account_id=account_id,
                    channel_id=other_private_id,
                )
            assert hidden.value.code == "CHANNEL_NOT_AVAILABLE"

            selected_rv = await select_channel(
                db,
                account_id=account_id,
                channel_id=RV_CHANNEL_ID,
            )
            replayed_rv = await select_channel(
                db,
                account_id=account_id,
                channel_id=RV_CHANNEL_ID,
            )
            assert selected_rv.selection_version == 2
            assert replayed_rv.selection_version == 2
            assert replayed_rv.selected_at == selected_rv.selected_at

            now = datetime.now(UTC)
            grant = MediaGrant(
                account_id=account_id,
                device_id=device_id,
                channel_id=RV_CHANNEL_ID,
                grant_kind="receive",
                provider="livekit",
                provider_room_ref="room_channel_database",
                provider_participant_ref=f"participant_{marker}",
                action_scope="subscribe",
                policy_version="ptt-v1",
                idempotency_key_hash="a" * 64,
                request_fingerprint="b" * 64,
                issued_at=now,
                expires_at=now + timedelta(minutes=5),
                outcome_code="issued",
            )
            db.add(grant)
            await db.commit()
            grant_id = grant.id
            switched_private = await select_channel(
                db,
                account_id=account_id,
                channel_id=private_id,
                now=now,
            )
            assert switched_private.selection_version == 3
            stored_receive = await db.get(MediaGrant, grant_id)
            assert stored_receive is not None
            await db.refresh(stored_receive)
            assert stored_receive.revoked_at == now
            assert stored_receive.outcome_code == "channel_switched"

            provider = FakeMediaProvider(now=lambda: now)
            fresh_receive = await create_receive_grant(
                db,
                account_id=account_id,
                device_id=device_id,
                idempotency_key="channel-switch-fresh-authority",
                settings=settings,
                provider=provider,
                now=now,
                random_ref=lambda: "channel-switch-fresh",
            )
            assert fresh_receive.grant_id != grant_id
            assert fresh_receive.room_ref == private.provider_room_ref
            assert provider.receive_requests[-1].room_ref == private.provider_room_ref

            transmit = MediaGrant(
                account_id=account_id,
                device_id=device_id,
                channel_id=private_id,
                parent_grant_id=fresh_receive.grant_id,
                grant_kind="transmit",
                provider="livekit",
                provider_room_ref=private.provider_room_ref,
                provider_participant_ref=f"participant_transmit_{marker}",
                action_scope="microphone_publish",
                policy_version="ptt-v1",
                idempotency_key_hash="c" * 64,
                request_fingerprint="d" * 64,
                issued_at=now,
                expires_at=now + timedelta(minutes=5),
                outcome_code="issued",
            )
            db.add(transmit)
            await db.commit()
            transmit_id = transmit.id
            with pytest.raises(ChannelError) as active_media:
                await select_channel(
                    db,
                    account_id=account_id,
                    channel_id=GENERAL_CHANNEL_ID,
                    now=now,
                )
            assert active_media.value.code == "CHANNEL_MEDIA_ACTIVE"
            await db.execute(
                update(MediaGrant)
                .where(MediaGrant.id == transmit_id)
                .values(revoked_at=now, outcome_code="released")
            )
            await db.commit()

        async def choose(channel_id: uuid.UUID) -> int:
            async with factory() as concurrent_db:
                receipt = await select_channel(
                    concurrent_db,
                    account_id=account_id,
                    channel_id=channel_id,
                )
                return receipt.selection_version

        versions = await asyncio.gather(
            choose(GENERAL_CHANNEL_ID),
            choose(private_id),
        )
        assert sorted(versions) == [4, 5]

        async with factory() as db:
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(ChannelSelection)
                    .where(ChannelSelection.account_id == account_id)
                )
                == 1
            )
            final = await db.scalar(
                select(ChannelSelection).where(ChannelSelection.account_id == account_id)
            )
            assert final is not None
            assert final.channel_id in {GENERAL_CHANNEL_ID, private_id}
            assert final.version == 5

            stored_grant = await db.scalar(select(MediaGrant).where(MediaGrant.id == grant_id))
            assert stored_grant is not None
            assert stored_grant.channel_id == RV_CHANNEL_ID
    finally:
        async with factory() as db:
            await db.execute(
                delete(ChannelSelection).where(ChannelSelection.account_id.in_(cleanup_account_ids))
            )
            await db.commit()
            for account_id in cleanup_account_ids:
                stored = await db.get(Account, account_id)
                if stored is not None:
                    await db.delete(stored)
            await db.commit()
        await engine.dispose()
