import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Account, ModerationReport, ModerationRestriction
from app.moderation.service import (
    ReportLifecycleError,
    RestrictionLifecycleError,
    set_restriction,
    submit_report,
)


def _db() -> MagicMock:
    db = MagicMock()
    db.get = AsyncMock()
    db.scalar = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


def _account(account_id: uuid.UUID) -> Account:
    return Account(id=account_id, status="active", account_type="anonymous")


def test_concurrent_identical_report_replays_after_unique_conflict() -> None:
    asyncio.run(_concurrent_identical_report_replays_after_unique_conflict())


async def _concurrent_identical_report_replays_after_unique_conflict() -> None:
    reporter_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    reporter = _account(reporter_id)
    subject = _account(subject_id)
    replay = ModerationReport(
        id=uuid.uuid4(),
        reporter_account_id=reporter_id,
        subject_account_id=subject_id,
        reason="spam",
        state="submitted",
        idempotency_key_hash="a" * 64,
    )
    db = _db()
    db.get.return_value = subject
    db.scalar.side_effect = [None, replay]
    db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("conflict"))

    result = await submit_report(
        db,
        reporter=reporter,
        subject_account_id=subject_id,
        reason="spam",
        idempotency_key="concurrent-report-0001",
    )

    assert result is replay
    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


def test_concurrent_mismatched_report_fails_with_generic_error() -> None:
    asyncio.run(_concurrent_mismatched_report_fails_with_generic_error())


async def _concurrent_mismatched_report_fails_with_generic_error() -> None:
    reporter_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    reporter = _account(reporter_id)
    subject = _account(subject_id)
    replay = ModerationReport(
        id=uuid.uuid4(),
        reporter_account_id=reporter_id,
        subject_account_id=subject_id,
        reason="harassment",
        state="submitted",
        idempotency_key_hash="b" * 64,
    )
    db = _db()
    db.get.return_value = subject
    db.scalar.side_effect = [None, replay]
    db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("conflict"))

    with pytest.raises(ReportLifecycleError, match="^report unavailable$"):
        await submit_report(
            db,
            reporter=reporter,
            subject_account_id=subject_id,
            reason="spam",
            idempotency_key="concurrent-report-0002",
        )

    db.rollback.assert_awaited_once()


def test_concurrent_identical_restriction_replays_after_unique_conflict() -> None:
    asyncio.run(_concurrent_identical_restriction_replays_after_unique_conflict())


async def _concurrent_identical_restriction_replays_after_unique_conflict() -> None:
    actor_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    actor = _account(actor_id)
    subject = _account(subject_id)
    replay = ModerationRestriction(
        id=uuid.uuid4(),
        actor_account_id=actor_id,
        subject_account_id=subject_id,
        kind="block",
        state="active",
    )
    db = _db()
    db.get.return_value = subject
    db.scalar.side_effect = [None, replay]
    db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("conflict"))

    result = await set_restriction(
        db,
        actor=actor,
        subject_account_id=subject_id,
        kind="block",
    )

    assert result is replay
    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


def test_concurrent_restriction_conflict_fails_with_generic_error() -> None:
    asyncio.run(_concurrent_restriction_conflict_fails_with_generic_error())


async def _concurrent_restriction_conflict_fails_with_generic_error() -> None:
    actor_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    actor = _account(actor_id)
    subject = _account(subject_id)
    db = _db()
    db.get.return_value = subject
    db.scalar.side_effect = [None, None]
    db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("conflict"))

    with pytest.raises(RestrictionLifecycleError, match="^moderation unavailable$"):
        await set_restriction(
            db,
            actor=actor,
            subject_account_id=subject_id,
            kind="mute",
        )

    db.rollback.assert_awaited_once()
