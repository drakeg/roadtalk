import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.location.nearby import NearbySummaryError, get_nearby_summary, nearby_bucket


def test_nearby_bucket_has_stable_semantic_boundaries() -> None:
    assert nearby_bucket(0, many_threshold=5) == "none"
    assert nearby_bucket(1, many_threshold=5) == "few"
    assert nearby_bucket(4, many_threshold=5) == "few"
    assert nearby_bucket(5, many_threshold=5) == "many"


def test_nearby_summary_fails_closed_without_usable_caller() -> None:
    asyncio.run(_missing_caller())


async def _missing_caller() -> None:
    db = AsyncMock()
    db.scalar.return_value = None

    with pytest.raises(NearbySummaryError):
        await get_nearby_summary(
            db,
            account_id=uuid.uuid4(),
            policy_version="location-v1",
            max_usable_accuracy_m=100,
            radius_m=5_000,
            many_threshold=5,
            now=datetime(2026, 7, 15, 12, tzinfo=UTC),
        )

    db.scalar.assert_awaited_once()


def test_nearby_summary_does_not_expose_internal_count_or_threshold() -> None:
    asyncio.run(_private_summary())


async def _private_summary() -> None:
    expires_at = datetime(2026, 7, 15, 12, 2, tzinfo=UTC)
    db = AsyncMock()
    db.scalar.side_effect = [
        SimpleNamespace(position=object(), expires_at=expires_at),
        4,
    ]

    summary = await get_nearby_summary(
        db,
        account_id=uuid.uuid4(),
        policy_version="location-v1",
        max_usable_accuracy_m=100,
        radius_m=5_000,
        many_threshold=5,
        now=datetime(2026, 7, 15, 12, tzinfo=UTC),
    )

    assert summary.bucket == "few"
    assert summary.expires_at == expires_at
    assert set(summary.__dict__) == {"availability", "bucket", "freshness", "expires_at"}
