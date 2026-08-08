import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import MediaGrant
from app.ptt.provider import FakeMediaProvider, MediaProviderError, MicrophonePublishRequest
from app.ptt.proximity import EligibleReceiveGrant, ProximityEligibilityError
from app.ptt.service import reconcile_proximity_delivery, release_transmit_grant


def published_transmit(*, now: datetime) -> MediaGrant:
    return MediaGrant(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        parent_grant_id=uuid.uuid4(),
        grant_kind="transmit",
        provider="livekit",
        provider_room_ref="room_opaque",
        provider_participant_ref="sender_opaque",
        provider_track_ref="track_opaque",
        action_scope="microphone_publish",
        policy_version="ptt-v1",
        proximity_policy_version="proximity-v1",
        eligibility_evaluated_at=now,
        idempotency_key_hash="a" * 64,
        request_fingerprint="b" * 64,
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(seconds=29),
        revoked_at=None,
        outcome_code="delivery_ready",
    )


def database_with(*grants: MediaGrant) -> AsyncMock:
    db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.all.return_value = list(grants)
    db.scalars.return_value = result
    return db


def eligible(*participant_refs: str) -> tuple[EligibleReceiveGrant, ...]:
    return tuple(
        EligibleReceiveGrant(
            receive_grant_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
            participant_ref=participant_ref,
        )
        for participant_ref in participant_refs
    )


def test_reconciliation_denies_locally_then_applies_exact_current_audience() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 7, 12, tzinfo=UTC)
        grant = published_transmit(now=now)
        db = database_with(grant)
        events: list[str] = []
        db.commit.side_effect = lambda: events.append(f"commit:{grant.outcome_code}")
        provider = FakeMediaProvider()
        original_update = provider.update_track_subscriptions

        async def update(request: object) -> None:
            events.append("provider")
            await original_update(request)  # type: ignore[arg-type]

        provider.update_track_subscriptions = update  # type: ignore[method-assign]
        receipt = await reconcile_proximity_delivery(
            db,
            provider=provider,
            settings=Settings(environment="test"),
            eligibility_finder=AsyncMock(return_value=eligible("listener_keep")),
            participant_finder=AsyncMock(return_value=("listener_drop", "listener_keep")),
            now=now,
        )

        assert events[0] == "commit:delivery_reconciling"
        assert events.index("commit:delivery_reconciling") < events.index("provider")
        assert [request.action for request in provider.subscription_requests] == [
            "unsubscribe",
            "subscribe",
        ]
        assert provider.subscription_requests[0].participant_refs == ("listener_drop",)
        assert provider.subscription_requests[1].participant_refs == ("listener_keep",)
        assert grant.outcome_code == "delivery_ready"
        assert receipt.transmissions_ready == 1
        assert receipt.transmissions_pending == 0

    asyncio.run(exercise())


def test_empty_audience_unsubscribes_and_ends_publication() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 7, 12, tzinfo=UTC)
        grant = published_transmit(now=now)
        provider = FakeMediaProvider()

        receipt = await reconcile_proximity_delivery(
            database_with(grant),
            provider=provider,
            settings=Settings(environment="test"),
            eligibility_finder=AsyncMock(return_value=()),
            participant_finder=AsyncMock(return_value=("listener_opaque",)),
            now=now,
        )

        assert grant.revoked_at == now
        assert grant.outcome_code == "no_nearby_listeners"
        assert provider.subscription_requests[0].action == "unsubscribe"
        assert provider.publish_requests[-1].enabled is False
        assert receipt.transmissions_ended == 1

    asyncio.run(exercise())


def test_transmit_release_unsubscribes_track_before_revoking_publish() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 7, 12, tzinfo=UTC)
        grant = published_transmit(now=now)
        db = AsyncMock(spec=AsyncSession)
        db.scalar.return_value = grant
        provider = FakeMediaProvider()
        track_ref = grant.provider_track_ref
        assert track_ref is not None
        provider.subscriptions[(grant.provider_room_ref, track_ref)] = frozenset(
            {"listener_opaque"}
        )

        receipt = await release_transmit_grant(
            db,
            account_id=grant.account_id,
            device_id=grant.device_id,
            grant_id=grant.id,
            provider=provider,
            participant_finder=AsyncMock(return_value=("listener_opaque",)),
            now=now,
        )

        assert receipt.replayed is False
        assert provider.subscription_requests[0].action == "unsubscribe"
        assert provider.subscriptions[(grant.provider_room_ref, track_ref)] == (frozenset())
        assert provider.publish_requests[-1].enabled is False

    asyncio.run(exercise())


class FailingCleanupProvider(FakeMediaProvider):
    async def update_track_subscriptions(self, request: object) -> None:
        del request
        raise MediaProviderError("synthetic reconciliation failure")

    async def set_microphone_publish(self, request: MicrophonePublishRequest) -> None:
        self.publish_requests.append(request)
        raise MediaProviderError("synthetic microphone cleanup failure")


@pytest.mark.parametrize(
    "finder_error",
    [ProximityEligibilityError(), MediaProviderError("synthetic")],
)
def test_unknown_or_provider_degraded_state_stays_pending_and_fail_closed(
    finder_error: Exception,
) -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 7, 12, tzinfo=UTC)
        grant = published_transmit(now=now)
        provider = FailingCleanupProvider()
        finder = AsyncMock(side_effect=finder_error)

        receipt = await reconcile_proximity_delivery(
            database_with(grant),
            provider=provider,
            settings=Settings(environment="test"),
            eligibility_finder=finder,
            participant_finder=AsyncMock(return_value=("listener_opaque",)),
            now=now,
        )

        assert grant.outcome_code == "delivery_reconciling"
        assert receipt.transmissions_pending == 1
        assert provider.publish_requests[-1].enabled is False

    asyncio.run(exercise())


@pytest.mark.parametrize("limit", [0, 1_001])
def test_reconciliation_rejects_unbounded_work(limit: int) -> None:
    db = AsyncMock(spec=AsyncSession)
    with pytest.raises(ValueError, match="between 1 and 1000"):
        asyncio.run(
            reconcile_proximity_delivery(
                db,
                provider=FakeMediaProvider(),
                settings=Settings(environment="test"),
                limit=limit,
            )
        )
    db.scalars.assert_not_awaited()
