import asyncio
import uuid
from unittest.mock import AsyncMock

from app.identity.service import callsign_availability


def test_invalid_and_reserved_callsigns_do_not_query_database() -> None:
    db = AsyncMock()

    invalid = asyncio.run(callsign_availability(db, account_id=uuid.uuid4(), candidate="not valid"))
    reserved = asyncio.run(
        callsign_availability(db, account_id=uuid.uuid4(), candidate="roadtalk-help")
    )

    assert invalid.model_dump() == {"available": False, "reason": "invalid"}
    assert reserved.model_dump() == {"available": False, "reason": "reserved"}
    db.scalar.assert_not_awaited()


def test_available_callsign_returns_only_availability_and_reason() -> None:
    db = AsyncMock()
    db.scalar.return_value = None

    result = asyncio.run(
        callsign_availability(db, account_id=uuid.uuid4(), candidate="Road-Runner")
    )

    assert result.model_dump() == {"available": True, "reason": "available"}
    db.scalar.assert_awaited_once()


def test_taken_callsign_does_not_disclose_owner() -> None:
    db = AsyncMock()
    db.scalar.return_value = uuid.uuid4()

    result = asyncio.run(
        callsign_availability(db, account_id=uuid.uuid4(), candidate="Road-Runner")
    )

    assert result.model_dump() == {"available": False, "reason": "taken"}
    assert set(result.model_dump()) == {"available", "reason"}
