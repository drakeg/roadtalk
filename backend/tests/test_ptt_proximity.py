import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from geoalchemy2 import WKTElement
from geoalchemy2.elements import WKBElement
from pydantic_core import ValidationError
from sqlalchemy.dialects.postgresql.base import PGDialect

from app.config import Settings
from app.ptt.proximity import (
    EligibleReceiveGrant,
    ProximityEligibilityError,
    directions_compatible,
    filter_same_road_receive_grants,
    find_eligible_receive_grants,
    proximity_policy_from_settings,
)


def test_proximity_policy_is_versioned_server_configuration() -> None:
    settings = Settings(environment="test")

    policy = proximity_policy_from_settings(settings)

    assert policy.version == "proximity-v1"
    assert policy.radius_m == 5_000
    assert policy.delivery_window_seconds == 30
    assert policy.location_policy_version == "location-v1"
    assert policy.ptt_policy_version == "ptt-v1"
    assert policy.max_usable_accuracy_m == 100
    assert policy.room_ref == settings.ptt_controlled_room_ref
    assert str(policy.channel_id) == "00000000-0000-4000-8000-000000000001"


def test_location_ttl_must_support_the_complete_delivery_window() -> None:
    with pytest.raises(ValidationError, match="must not exceed location_usable"):
        Settings(
            environment="test",
            location_usable_ttl_seconds=20,
            location_degraded_ttl_seconds=20,
            ptt_transmit_grant_ttl_seconds=30,
        )


def test_proximity_query_fails_closed_without_sender_location() -> None:
    asyncio.run(_missing_sender())


async def _missing_sender() -> None:
    db = AsyncMock()
    db.scalar.return_value = None

    with pytest.raises(ProximityEligibilityError):
        await find_eligible_receive_grants(
            db,
            sender_account_id=uuid.uuid4(),
            sender_device_id=uuid.uuid4(),
            policy=proximity_policy_from_settings(Settings(environment="test")),
            now=datetime(2026, 8, 6, 1, tzinfo=UTC),
        )

    db.scalar.assert_awaited_once()
    db.execute.assert_not_awaited()


def test_proximity_query_returns_only_transient_opaque_receiver_metadata() -> None:
    asyncio.run(_private_eligibility())


async def _private_eligibility() -> None:
    sender_account_id = uuid.uuid4()
    sender_device_id = uuid.uuid4()
    receive_grant_id = uuid.uuid4()
    recipient_account_id = uuid.uuid4()
    recipient_device_id = uuid.uuid4()
    sender_position = WKTElement("POINT(-75 40)", srid=4326)
    proximity_result = SimpleNamespace(
        all=lambda: [
            (
                receive_grant_id,
                recipient_account_id,
                recipient_device_id,
                "participant_opaque_receiver",
            )
        ]
    )
    nearby_modes = SimpleNamespace(all=lambda: [])
    db = AsyncMock()
    db.scalar.return_value = SimpleNamespace(position=sender_position)
    db.execute.side_effect = [proximity_result, nearby_modes]

    eligible = await find_eligible_receive_grants(
        db,
        sender_account_id=sender_account_id,
        sender_device_id=sender_device_id,
        policy=proximity_policy_from_settings(Settings(environment="test")),
        now=datetime(2026, 8, 6, 1, tzinfo=UTC),
    )

    assert len(eligible) == 1
    assert eligible[0].receive_grant_id == receive_grant_id
    assert eligible[0].account_id == recipient_account_id
    assert eligible[0].device_id == recipient_device_id
    assert eligible[0].participant_ref == "participant_opaque_receiver"
    assert set(eligible[0].__dict__) == {
        "receive_grant_id",
        "account_id",
        "device_id",
        "participant_ref",
    }

    statement = db.execute.await_args_list[0].args[0]
    compiled = str(
        statement.compile(
            dialect=PGDialect(),  # type: ignore[no-untyped-call]
            compile_kwargs={"render_postcompile": True},
        )
    ).lower()
    assert "st_dwithin" in compiled
    assert "current_location.source_device_id = media_grant.device_id" in compiled
    assert "media_grant.grant_kind" in compiled
    assert "media_grant.provider_room_ref" in compiled
    assert "media_grant.channel_id" in compiled
    assert "channel_selection.channel_id = media_grant.channel_id" in compiled
    assert "channel_membership.state" in compiled
    assert "channel.provider_room_ref" in compiled
    assert "session.revoked_at is null" in compiled
    assert "account.status" in compiled
    assert "distance" not in compiled
    assert "st_distance" not in compiled
    assert "latitude" not in compiled
    assert "longitude" not in compiled


def test_eligible_receiver_shape_cannot_include_location_values() -> None:
    annotations = EligibleReceiveGrant.__annotations__
    assert annotations == {
        "receive_grant_id": uuid.UUID,
        "account_id": uuid.UUID,
        "device_id": uuid.UUID,
        "participant_ref": str,
    }
    assert WKBElement not in annotations.values()


def test_same_road_direction_policy_is_coarse_and_wraparound_safe() -> None:
    assert directions_compatible("north", "north")
    assert directions_compatible("north", "northeast")
    assert directions_compatible("north", "northwest")
    assert directions_compatible("northwest", "north")
    assert not directions_compatible("north", "east")
    assert not directions_compatible("north", "south")
    assert not directions_compatible("stationary", "north")
    assert not directions_compatible("unknown", "north")
    assert not directions_compatible("stationary", "stationary")


def test_same_road_filter_can_only_reduce_prior_eligibility() -> None:
    asyncio.run(_same_road_filter_matrix())


async def _same_road_filter_matrix() -> None:
    sender_account_id = uuid.uuid4()
    receiver_account_id = uuid.uuid4()
    receiver = EligibleReceiveGrant(
        receive_grant_id=uuid.uuid4(),
        account_id=receiver_account_id,
        device_id=uuid.uuid4(),
        participant_ref="participant_receiver",
    )
    now = datetime(2026, 8, 25, 12, tzinfo=UTC)

    async def evaluate(
        *,
        sender_mode: str,
        receiver_mode: str,
        sender_corridor: str | None,
        receiver_corridor: str | None,
        sender_direction: str = "north",
        receiver_direction: str = "northwest",
    ) -> tuple[EligibleReceiveGrant, ...]:
        modes = SimpleNamespace(
            all=lambda: [
                (sender_account_id, sender_mode),
                (receiver_account_id, receiver_mode),
            ]
        )
        contexts = []
        if sender_corridor is not None:
            contexts.append(
                SimpleNamespace(
                    account_id=sender_account_id,
                    corridor_digest=sender_corridor,
                    direction=sender_direction,
                )
            )
        if receiver_corridor is not None:
            contexts.append(
                SimpleNamespace(
                    account_id=receiver_account_id,
                    corridor_digest=receiver_corridor,
                    direction=receiver_direction,
                )
            )
        db = AsyncMock()
        db.execute.return_value = modes
        db.scalars.return_value = SimpleNamespace(all=lambda: contexts)
        return await filter_same_road_receive_grants(
            db,
            sender_account_id=sender_account_id,
            eligible_receivers=(receiver,),
            now=now,
        )

    assert await evaluate(
        sender_mode="nearby",
        receiver_mode="nearby",
        sender_corridor=None,
        receiver_corridor=None,
    ) == (receiver,)
    assert await evaluate(
        sender_mode="same_road",
        receiver_mode="nearby",
        sender_corridor="a" * 64,
        receiver_corridor="a" * 64,
    ) == (receiver,)
    assert await evaluate(
        sender_mode="nearby",
        receiver_mode="same_road",
        sender_corridor="a" * 64,
        receiver_corridor="a" * 64,
    ) == (receiver,)
    assert await evaluate(
        sender_mode="same_road",
        receiver_mode="same_road",
        sender_corridor="a" * 64,
        receiver_corridor="b" * 64,
    ) == ()
    assert await evaluate(
        sender_mode="same_road",
        receiver_mode="same_road",
        sender_corridor=None,
        receiver_corridor="a" * 64,
    ) == ()
    assert await evaluate(
        sender_mode="same_road",
        receiver_mode="same_road",
        sender_corridor="a" * 64,
        receiver_corridor="a" * 64,
        receiver_direction="unknown",
    ) == ()

    denied_before_route_filter: tuple[EligibleReceiveGrant, ...] = ()
    db = AsyncMock()
    assert await filter_same_road_receive_grants(
        db,
        sender_account_id=sender_account_id,
        eligible_receivers=denied_before_route_filter,
        now=now,
    ) == ()
    db.execute.assert_not_awaited()
    db.scalars.assert_not_awaited()
