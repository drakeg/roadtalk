import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.route_context.lifecycle import delete_expired_route_contexts


def test_expired_route_context_cleanup_is_bounded_and_committed() -> None:
    async def exercise() -> None:
        db = AsyncMock(spec=AsyncSession)
        db.scalars.return_value = SimpleNamespace(all=lambda: ["a", "b"])

        deleted = await delete_expired_route_contexts(
            db,
            now=datetime(2026, 8, 25, 22, tzinfo=UTC),
            limit=2,
        )

        assert deleted == 2
        db.scalars.assert_awaited_once()
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

    asyncio.run(exercise())


def test_expired_route_context_cleanup_handles_empty_batch_without_delete() -> None:
    async def exercise() -> None:
        db = AsyncMock(spec=AsyncSession)
        db.scalars.return_value = SimpleNamespace(all=lambda: [])

        deleted = await delete_expired_route_contexts(db, limit=100)

        assert deleted == 0
        db.execute.assert_not_awaited()
        db.commit.assert_awaited_once()

    asyncio.run(exercise())


@pytest.mark.parametrize("limit", [0, 1_001])
def test_expired_route_context_cleanup_rejects_unbounded_work(limit: int) -> None:
    db = AsyncMock(spec=AsyncSession)
    with pytest.raises(ValueError, match="between 1 and 1000"):
        asyncio.run(delete_expired_route_contexts(db, limit=limit))
    db.scalars.assert_not_awaited()
    db.execute.assert_not_awaited()
    db.commit.assert_not_awaited()
