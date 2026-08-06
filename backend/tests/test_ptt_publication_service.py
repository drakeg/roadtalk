import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import MediaGrant
from app.ptt.provider import FakeMediaProvider, ProviderTrackState
from app.ptt.proximity import EligibleReceiveGrant, ProximityEligibilityError
from app.ptt.service import GrantError, publish_transmit_track


def transmit_grant(*, now: datetime, published_track_ref: str | None = None) -> MediaGrant:
    return MediaGrant(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        parent_grant_id=uuid.uuid4(),
        grant_kind="transmit",
        provider="livekit",
        provider_room_ref="room_opaque",
        provider_participant_ref="publisher_opaque",
        provider_track_ref=published_track_ref,
        action_scope="microphone_publish",
        policy_version="ptt-v1",
        proximity_policy_version="proximity-v1" if published_track_ref else None,
        eligibility_evaluated_at=now if published_track_ref else None,
        idempotency_key_hash="a" * 64,
        request_fingerprint="b" * 64,
        issued_at=now,
        expires_at=now + timedelta(seconds=30),
        revoked_at=None,
        outcome_code="delivery_ready" if published_track_ref else "issued",
    )


def publication_db(grant: MediaGrant) -> AsyncMock:
    db = AsyncMock(spec=AsyncSession)
    db.scalar.side_effect = [grant.account_id, grant]
    return db


def provider_for(
    grant: MediaGrant, *, fail_calls: frozenset[int] = frozenset()
) -> FakeMediaProvider:
    return FakeMediaProvider(
        tracks=(
            ProviderTrackState(
                room_ref=grant.provider_room_ref,
                participant_ref=grant.provider_participant_ref,
                track_ref="microphone_track_opaque",
                source="microphone",
                active=True,
            ),
        ),
        fail_subscription_calls=fail_calls,
    )


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


def test_publication_verifies_then_recomputes_and_subscribes_only_current_audience() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 6, 4, tzinfo=UTC)
        grant = transmit_grant(now=now)
        db = publication_db(grant)
        provider = provider_for(grant)
        finder = AsyncMock(return_value=eligible("listener_2", "listener_1", "listener_2"))

        receipt = await publish_transmit_track(
            db,
            account_id=grant.account_id,
            device_id=grant.device_id,
            transmit_grant_id=grant.id,
            track_ref="microphone_track_opaque",
            settings=Settings(environment="test"),
            provider=provider,
            eligibility_finder=finder,
            now=now,
        )

        assert receipt.delivery_state == "ready"
        assert receipt.proximity_policy_version == "proximity-v1"
        assert receipt.evaluated_at == now
        assert receipt.replayed is False
        assert provider.track_lookup_requests[0].room_ref == grant.provider_room_ref
        assert provider.track_lookup_requests[0].participant_ref == grant.provider_participant_ref
        assert provider.subscription_requests[0].participant_refs == (
            "listener_1",
            "listener_2",
        )
        assert provider.subscriptions[(grant.provider_room_ref, "microphone_track_opaque")] == (
            frozenset({"listener_1", "listener_2"})
        )
        assert grant.provider_track_ref == "microphone_track_opaque"
        assert grant.outcome_code == "delivery_ready"
        finder.assert_awaited_once()

    asyncio.run(exercise())


def test_publication_replay_is_provider_free_and_conflicting_track_fails_closed() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 6, 4, tzinfo=UTC)
        grant = transmit_grant(now=now, published_track_ref="microphone_track_opaque")
        provider = FakeMediaProvider()
        replay = await publish_transmit_track(
            publication_db(grant),
            account_id=grant.account_id,
            device_id=grant.device_id,
            transmit_grant_id=grant.id,
            track_ref="microphone_track_opaque",
            settings=Settings(environment="test"),
            provider=provider,
            now=now,
        )
        assert replay.replayed is True
        assert replay.delivery_state == "ready"
        assert provider.track_lookup_requests == []
        assert provider.subscription_requests == []

        with pytest.raises(GrantError) as conflict:
            await publish_transmit_track(
                publication_db(grant),
                account_id=grant.account_id,
                device_id=grant.device_id,
                transmit_grant_id=grant.id,
                track_ref="different_track_opaque",
                settings=Settings(environment="test"),
                provider=provider,
                now=now,
            )
        assert conflict.value.code == "PTT_PUBLICATION_CONFLICT"

    asyncio.run(exercise())


def test_publication_empty_audience_records_metadata_without_subscription() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 6, 4, tzinfo=UTC)
        grant = transmit_grant(now=now)
        provider = provider_for(grant)

        receipt = await publish_transmit_track(
            publication_db(grant),
            account_id=grant.account_id,
            device_id=grant.device_id,
            transmit_grant_id=grant.id,
            track_ref="microphone_track_opaque",
            settings=Settings(environment="test"),
            provider=provider,
            eligibility_finder=AsyncMock(return_value=()),
            now=now,
        )

        assert receipt.delivery_state == "no_nearby_listeners"
        assert grant.provider_track_ref == "microphone_track_opaque"
        assert provider.subscription_requests == []

    asyncio.run(exercise())


def test_publication_provider_failure_compensates_and_marks_reconciling() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 6, 4, tzinfo=UTC)
        grant = transmit_grant(now=now)
        provider = provider_for(grant, fail_calls=frozenset({1}))

        with pytest.raises(GrantError) as unavailable:
            await publish_transmit_track(
                publication_db(grant),
                account_id=grant.account_id,
                device_id=grant.device_id,
                transmit_grant_id=grant.id,
                track_ref="microphone_track_opaque",
                settings=Settings(environment="test"),
                provider=provider,
                eligibility_finder=AsyncMock(return_value=eligible("listener_1")),
                now=now,
            )

        assert unavailable.value.code == "PTT_PROVIDER_UNAVAILABLE"
        assert [request.action for request in provider.subscription_requests] == [
            "subscribe",
            "unsubscribe",
        ]
        assert provider.subscriptions[(grant.provider_room_ref, "microphone_track_opaque")] == (
            frozenset()
        )
        assert grant.outcome_code == "delivery_reconciling"

    asyncio.run(exercise())


def test_publication_rejects_unverified_track_and_unusable_location() -> None:
    async def exercise() -> None:
        now = datetime(2026, 8, 6, 4, tzinfo=UTC)
        grant = transmit_grant(now=now)
        with pytest.raises(GrantError) as invalid:
            await publish_transmit_track(
                publication_db(grant),
                account_id=grant.account_id,
                device_id=grant.device_id,
                transmit_grant_id=grant.id,
                track_ref="unknown_track_opaque",
                settings=Settings(environment="test"),
                provider=provider_for(grant),
                now=now,
            )
        assert invalid.value.code == "PTT_TRACK_INVALID"

        with pytest.raises(GrantError) as location:
            await publish_transmit_track(
                publication_db(grant),
                account_id=grant.account_id,
                device_id=grant.device_id,
                transmit_grant_id=grant.id,
                track_ref="microphone_track_opaque",
                settings=Settings(environment="test"),
                provider=provider_for(grant),
                eligibility_finder=AsyncMock(side_effect=ProximityEligibilityError),
                now=now,
            )
        assert location.value.code == "PTT_LOCATION_UNAVAILABLE"

    asyncio.run(exercise())
