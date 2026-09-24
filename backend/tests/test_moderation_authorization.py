import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.ptt.proximity import EligibleReceiveGrant, filter_moderation_receive_grants


def _receiver(account_id: uuid.UUID) -> EligibleReceiveGrant:
    return EligibleReceiveGrant(uuid.uuid4(), account_id, uuid.uuid4(), "participant")


def test_moderation_filter_never_adds_upstream_ineligible_recipient() -> None:
    asyncio.run(_never_adds_recipient())


async def _never_adds_recipient() -> None:
    keep = _receiver(uuid.uuid4())
    db = AsyncMock()
    result_proxy = MagicMock()
    result_proxy.all.return_value = []
    db.execute.return_value = result_proxy

    result = await filter_moderation_receive_grants(
        db,
        sender_account_id=uuid.uuid4(),
        eligible_receivers=(keep,),
        now=datetime.now(UTC),
    )

    assert result == (keep,)
    assert set(result).issubset({keep})


def test_receiver_mute_or_block_of_sender_denies_delivery() -> None:
    asyncio.run(_receiver_restrictions())


async def _receiver_restrictions() -> None:
    sender_id = uuid.uuid4()
    muted = _receiver(uuid.uuid4())
    blocked = _receiver(uuid.uuid4())
    keep = _receiver(uuid.uuid4())
    db = AsyncMock()
    result_proxy = MagicMock()
    result_proxy.all.return_value = [
        SimpleNamespace(
            actor_account_id=muted.account_id,
            subject_account_id=sender_id,
            kind="mute",
        ),
        SimpleNamespace(
            actor_account_id=blocked.account_id,
            subject_account_id=sender_id,
            kind="block",
        ),
    ]
    db.execute.return_value = result_proxy

    result = await filter_moderation_receive_grants(
        db,
        sender_account_id=sender_id,
        eligible_receivers=(muted, blocked, keep),
        now=datetime.now(UTC),
    )

    assert result == (keep,)


def test_sender_block_denies_receiver_but_sender_mute_does_not_broaden_or_deny() -> None:
    asyncio.run(_sender_restrictions())


async def _sender_restrictions() -> None:
    sender_id = uuid.uuid4()
    blocked = _receiver(uuid.uuid4())
    muted = _receiver(uuid.uuid4())
    db = AsyncMock()
    result_proxy = MagicMock()
    result_proxy.all.return_value = [
        SimpleNamespace(
            actor_account_id=sender_id,
            subject_account_id=blocked.account_id,
            kind="block",
        ),
        SimpleNamespace(
            actor_account_id=sender_id,
            subject_account_id=muted.account_id,
            kind="mute",
        ),
    ]
    db.execute.return_value = result_proxy

    result = await filter_moderation_receive_grants(
        db,
        sender_account_id=sender_id,
        eligible_receivers=(blocked, muted),
        now=datetime.now(UTC),
    )

    assert result == (muted,)


def test_moderation_query_requires_active_unexpired_state() -> None:
    asyncio.run(_query_is_current_only())


async def _query_is_current_only() -> None:
    receiver = _receiver(uuid.uuid4())
    db = AsyncMock()
    result_proxy = MagicMock()
    result_proxy.all.return_value = []
    db.execute.return_value = result_proxy
    now = datetime.now(UTC)

    await filter_moderation_receive_grants(
        db,
        sender_account_id=uuid.uuid4(),
        eligible_receivers=(receiver,),
        now=now,
    )

    statement = str(db.execute.await_args.args[0])
    assert "state" in statement
    assert "expires_at" in statement
