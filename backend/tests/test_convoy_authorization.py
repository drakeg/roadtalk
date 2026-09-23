import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ptt.proximity import EligibleReceiveGrant, filter_convoy_receive_grants


def _receiver(account_id: uuid.UUID) -> EligibleReceiveGrant:
    return EligibleReceiveGrant(uuid.uuid4(), account_id, uuid.uuid4(), "participant")


@pytest.mark.asyncio
async def test_convoy_filter_never_adds_recipient_without_sender_context() -> None:
    receivers = (_receiver(uuid.uuid4()), _receiver(uuid.uuid4()))
    db = AsyncMock()
    db.scalar.return_value = None

    result = await filter_convoy_receive_grants(
        db,
        sender_account_id=uuid.uuid4(),
        eligible_receivers=receivers,
        now=datetime.now(UTC),
    )

    assert result == receivers


@pytest.mark.asyncio
async def test_convoy_filter_only_keeps_active_same_convoy_candidates() -> None:
    keep = _receiver(uuid.uuid4())
    remove = _receiver(uuid.uuid4())
    convoy_id = uuid.uuid4()
    db = AsyncMock()
    db.scalar.return_value = SimpleNamespace(convoy_id=convoy_id)
    scalars = AsyncMock()
    scalars.all.return_value = [keep.account_id]
    db.scalars.return_value = scalars

    result = await filter_convoy_receive_grants(
        db,
        sender_account_id=uuid.uuid4(),
        eligible_receivers=(keep, remove),
        now=datetime.now(UTC),
    )

    assert result == (keep,)
    assert set(result).issubset({keep, remove})


@pytest.mark.asyncio
async def test_convoy_filter_fails_closed_for_expired_membership_query() -> None:
    receiver = _receiver(uuid.uuid4())
    now = datetime.now(UTC)
    db = AsyncMock()
    db.scalar.return_value = SimpleNamespace(convoy_id=uuid.uuid4())
    scalars = AsyncMock()
    scalars.all.return_value = []
    db.scalars.return_value = scalars

    result = await filter_convoy_receive_grants(
        db,
        sender_account_id=uuid.uuid4(),
        eligible_receivers=(receiver,),
        now=now,
    )

    assert result == ()
    statement = db.scalars.await_args.args[0]
    assert "expires_at" in str(statement)
    assert now + timedelta(seconds=0) == now
