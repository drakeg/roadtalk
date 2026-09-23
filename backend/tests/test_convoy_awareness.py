import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.convoys.awareness import current_convoy_awareness


def test_non_member_gets_no_convoy_awareness() -> None:
    asyncio.run(_non_member())


async def _non_member() -> None:
    db = AsyncMock()
    db.scalar.return_value = None

    result = await current_convoy_awareness(
        db,
        viewer_account_id=uuid.uuid4(),
        location_policy_version="location-v1",
        now=datetime(2026, 9, 23, tzinfo=UTC),
    )

    assert result is None
    db.execute.assert_not_awaited()


def test_awareness_contains_only_bounded_member_state() -> None:
    asyncio.run(_bounded_member_state())


async def _bounded_member_state() -> None:
    now = datetime(2026, 9, 23, tzinfo=UTC)
    convoy_id = uuid.uuid4()
    member_id = uuid.uuid4()
    expires_at = now + timedelta(seconds=30)
    db = AsyncMock()
    db.scalar.return_value = SimpleNamespace(convoy_id=convoy_id)
    rows = SimpleNamespace(
        all=lambda: [
            SimpleNamespace(
                account_id=member_id,
                display_callsign="Mallard One",
                role="member",
                expires_at=expires_at,
            )
        ]
    )
    db.execute.return_value = rows

    result = await current_convoy_awareness(
        db,
        viewer_account_id=uuid.uuid4(),
        location_policy_version="location-v1",
        now=now,
    )

    assert result is not None
    assert result.convoy_id == convoy_id
    assert result.expires_at == expires_at
    assert len(result.members) == 1
    assert result.members[0].account_id == member_id
    assert result.members[0].callsign == "Mallard One"
    assert set(result.members[0].model_dump()) == {
        "account_id",
        "callsign",
        "role",
        "availability",
        "expires_at",
    }
    statement = str(db.execute.await_args.args[0])
    assert "current_location" in statement
    assert "location_consent_event" in statement
    assert "session" in statement
    assert "convoy_membership" in statement
    assert "position" not in statement
    assert "latitude" not in statement
    assert "longitude" not in statement


def test_empty_authorized_awareness_expires_immediately() -> None:
    asyncio.run(_empty_authorized())


async def _empty_authorized() -> None:
    now = datetime(2026, 9, 23, tzinfo=UTC)
    convoy_id = uuid.uuid4()
    db = AsyncMock()
    db.scalar.return_value = SimpleNamespace(convoy_id=convoy_id)
    db.execute.return_value = SimpleNamespace(all=lambda: [])

    result = await current_convoy_awareness(
        db,
        viewer_account_id=uuid.uuid4(),
        location_policy_version="location-v1",
        now=now,
    )

    assert result is not None
    assert result.members == ()
    assert result.expires_at == now
