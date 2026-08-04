import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MediaGrant
from app.ptt.provider import (
    FakeMediaProvider,
    MediaProviderError,
    MicrophonePublishRequest,
    ParticipantRequest,
)
from app.ptt.service import GrantError, reconcile_media_grants, release_transmit_grant


def grant(
    *,
    now: datetime,
    kind: str,
    participant: str,
    expired: bool = False,
    pending: bool = False,
) -> MediaGrant:
    issued_at = now - timedelta(minutes=5)
    return MediaGrant(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        parent_grant_id=uuid.uuid4() if kind == "transmit" else None,
        grant_kind=kind,
        provider="livekit",
        provider_room_ref="room_opaque",
        provider_participant_ref=participant,
        action_scope="microphone_publish" if kind == "transmit" else "subscribe",
        policy_version="ptt-v1",
        idempotency_key_hash="a" * 64,
        request_fingerprint="b" * 64,
        issued_at=issued_at,
        expires_at=now - timedelta(seconds=1) if expired else now + timedelta(minutes=1),
        revoked_at=now - timedelta(seconds=2) if pending else None,
        outcome_code="provider_cleanup_pending" if pending else "issued",
    )


class FailingCleanupProvider(FakeMediaProvider):
    async def set_microphone_publish(self, request: MicrophonePublishRequest) -> None:
        self.publish_requests.append(request)
        raise MediaProviderError("synthetic cleanup failure")


class FailingRemovalProvider(FakeMediaProvider):
    async def remove_participant(self, request: ParticipantRequest) -> None:
        self.remove_requests.append(request)
        raise MediaProviderError("synthetic participant removal failure")


def test_bounded_reconciliation_revokes_locally_before_provider_cleanup() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 3, 12, tzinfo=UTC)
        expired_receive = grant(
            now=now,
            kind="receive",
            participant="participant_expired",
            expired=True,
        )
        expired_transmit = grant(
            now=now,
            kind="transmit",
            participant="participant_expired",
            expired=True,
        )
        pending = grant(
            now=now,
            kind="receive",
            participant="participant_pending",
            pending=True,
        )
        db = AsyncMock(spec=AsyncSession)
        scalar_result = MagicMock()
        scalar_result.all.return_value = [
            expired_receive,
            expired_transmit,
            pending,
        ]
        db.scalars.return_value = scalar_result
        events: list[str] = []
        db.commit.side_effect = lambda: events.append("local_commit")
        provider = FakeMediaProvider(now=lambda: now)
        original_publish = provider.set_microphone_publish

        async def publish(request: MicrophonePublishRequest) -> None:
            events.append("provider_cleanup")
            await original_publish(request)

        provider.set_microphone_publish = publish  # type: ignore[method-assign]

        receipt = await reconcile_media_grants(
            db,
            provider=provider,
            now=now,
            limit=25,
        )

        assert events.index("local_commit") < events.index("provider_cleanup")
        assert receipt.grants_examined == 3
        assert receipt.grants_locally_revoked == 2
        assert receipt.participants_reconciled == 2
        assert receipt.participants_pending == 0
        assert expired_receive.revoked_at == now
        assert expired_transmit.revoked_at == now
        assert pending.outcome_code == "provider_reconciled"
        assert [request.enabled for request in provider.publish_requests] == [False, False]
        assert {request.participant_ref for request in provider.remove_requests} == {
            "participant_expired",
            "participant_pending",
        }

    asyncio.run(exercise())


def test_reconciliation_failure_remains_durably_pending() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 3, 12, tzinfo=UTC)
        stale = grant(
            now=now,
            kind="receive",
            participant="participant_stale",
            expired=True,
        )
        db = AsyncMock(spec=AsyncSession)
        scalar_result = MagicMock()
        scalar_result.all.return_value = [stale]
        db.scalars.return_value = scalar_result

        receipt = await reconcile_media_grants(
            db,
            provider=FailingCleanupProvider(now=lambda: now),
            now=now,
        )

        assert stale.revoked_at == now
        assert stale.outcome_code == "provider_cleanup_pending"
        assert receipt.participants_reconciled == 0
        assert receipt.participants_pending == 1
        assert db.commit.await_count == 2

    asyncio.run(exercise())


def test_partial_provider_cleanup_divergence_remains_pending() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 3, 12, tzinfo=UTC)
        stale = grant(
            now=now,
            kind="receive",
            participant="participant_partial_failure",
            expired=True,
        )
        db = AsyncMock(spec=AsyncSession)
        scalar_result = MagicMock()
        scalar_result.all.return_value = [stale]
        db.scalars.return_value = scalar_result
        provider = FailingRemovalProvider(now=lambda: now)

        receipt = await reconcile_media_grants(db, provider=provider, now=now)

        assert [request.enabled for request in provider.publish_requests] == [False]
        assert stale.revoked_at == now
        assert stale.outcome_code == "provider_cleanup_pending"
        assert receipt.participants_reconciled == 0
        assert receipt.participants_pending == 1

    asyncio.run(exercise())


def test_delayed_transmit_release_revokes_parent_and_requests_removal() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 3, 12, tzinfo=UTC)
        transmit = grant(
            now=now,
            kind="transmit",
            participant="participant_delayed",
        )
        db = AsyncMock(spec=AsyncSession)
        db.scalar.return_value = transmit
        provider = FailingCleanupProvider(now=lambda: now)

        with pytest.raises(GrantError) as failure:
            await release_transmit_grant(
                db,
                account_id=transmit.account_id,
                device_id=transmit.device_id,
                grant_id=transmit.id,
                provider=provider,
                now=now,
            )

        assert failure.value.code == "PTT_PROVIDER_UNAVAILABLE"
        assert transmit.revoked_at == now
        assert transmit.outcome_code == "provider_cleanup_pending"
        assert db.execute.await_count == 1
        statement = str(db.execute.await_args.args[0])
        assert "media_grant.id" in statement
        assert "media_grant.revoked_at IS NULL" in statement
        assert [request.participant_ref for request in provider.remove_requests] == [
            "participant_delayed"
        ]
        assert db.commit.await_count == 2

    asyncio.run(exercise())


@pytest.mark.parametrize("limit", [0, 1_001])
def test_reconciliation_rejects_unbounded_work(limit: int) -> None:
    db = AsyncMock(spec=AsyncSession)

    with pytest.raises(ValueError, match="between 1 and 1000"):
        asyncio.run(
            reconcile_media_grants(
                db,
                provider=FakeMediaProvider(),
                limit=limit,
            )
        )

    db.scalars.assert_not_awaited()
