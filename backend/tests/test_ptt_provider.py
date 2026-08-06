import asyncio
from datetime import UTC, datetime

import jwt
import pytest
from pydantic import SecretStr

from app.config import Settings
from app.ptt.provider import (
    DisabledMediaProvider,
    FakeMediaProvider,
    MediaProviderDisabledError,
    MediaProviderSubscriptionError,
    MediaProviderTrackVerificationError,
    MediaProviderUnavailableError,
    MicrophonePublishRequest,
    MicrophoneTrackLookupRequest,
    ParticipantRequest,
    ProviderTrackState,
    ReceiveCredentialRequest,
    SelectiveSubscriptionRequest,
    VerifiedMicrophoneTrack,
    media_provider_from_settings,
)


def test_disabled_provider_fails_closed_without_network() -> None:
    async def exercise() -> None:
        provider = DisabledMediaProvider()
        with pytest.raises(MediaProviderDisabledError, match="provider is disabled"):
            await provider.issue_receive_credential(
                ReceiveCredentialRequest(
                    room_ref="room_opaque_1",
                    participant_ref="participant_opaque_1",
                    ttl_seconds=300,
                )
            )
        with pytest.raises(MediaProviderDisabledError):
            await provider.set_microphone_publish(
                MicrophonePublishRequest(
                    room_ref="room_opaque_1",
                    participant_ref="participant_opaque_1",
                    enabled=True,
                )
            )
        with pytest.raises(MediaProviderDisabledError):
            await provider.remove_participant(
                ParticipantRequest(
                    room_ref="room_opaque_1",
                    participant_ref="participant_opaque_1",
                )
            )
        with pytest.raises(MediaProviderDisabledError):
            await provider.verify_microphone_track(
                MicrophoneTrackLookupRequest(
                    room_ref="room_opaque_1",
                    participant_ref="participant_opaque_1",
                    track_ref="track_opaque_1",
                )
            )
        with pytest.raises(MediaProviderDisabledError):
            await provider.update_track_subscriptions(
                SelectiveSubscriptionRequest(
                    track=VerifiedMicrophoneTrack(
                        room_ref="room_opaque_1",
                        participant_ref="participant_opaque_1",
                        track_ref="track_opaque_1",
                    ),
                    participant_refs=("participant_listener_1",),
                    action="subscribe",
                )
            )

    asyncio.run(exercise())


def test_fake_provider_is_deterministic_and_masks_token() -> None:
    fixed_now = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)

    async def exercise() -> None:
        provider = FakeMediaProvider(now=lambda: fixed_now)
        request = ReceiveCredentialRequest(
            room_ref="room_opaque_1",
            participant_ref="participant_opaque_1",
            ttl_seconds=300,
        )
        assert request.auto_subscribe is False
        credential = await provider.issue_receive_credential(request)
        publish = MicrophonePublishRequest(
            room_ref=request.room_ref,
            participant_ref=request.participant_ref,
            enabled=True,
        )
        remove = ParticipantRequest(
            room_ref=request.room_ref,
            participant_ref=request.participant_ref,
        )
        await provider.set_microphone_publish(publish)
        await provider.remove_participant(remove)

        assert provider.receive_requests == [request]
        assert provider.publish_requests == [publish]
        assert provider.remove_requests == [remove]
        assert credential.server_url == "wss://synthetic.invalid"
        assert credential.expires_at.timestamp() - fixed_now.timestamp() == 300
        assert isinstance(credential.participant_token, SecretStr)
        assert credential.participant_token.get_secret_value() not in repr(credential)
        claims = jwt.decode(
            credential.participant_token.get_secret_value(),
            "synthetic-livekit-secret-for-tests-only",
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_exp": False, "verify_nbf": False},
        )
        assert claims["sub"] == request.participant_ref
        assert claims["video"] == {
            "room": request.room_ref,
            "roomJoin": True,
            "canSubscribe": True,
            "canPublish": False,
            "canPublishData": False,
            "roomAdmin": False,
            "recorder": False,
        }
        assert "roomRecord" not in claims["video"]
        assert "egress" not in claims["video"]
        for forbidden_claim in (
            "canPublishSources",
            "hidden",
            "ingressAdmin",
            "roomCreate",
            "roomList",
            "roomRecord",
            "roomAdmin",
            "recorder",
        ):
            assert claims["video"].get(forbidden_claim) in (None, False)

    asyncio.run(exercise())


def test_fake_verifies_only_the_owned_active_microphone_track() -> None:
    async def exercise() -> None:
        states = (
            ProviderTrackState("room_1", "publisher_1", "microphone_1", "microphone", True),
            ProviderTrackState("room_1", "publisher_1", "camera_1", "camera", True),
            ProviderTrackState("room_1", "publisher_1", "ended_1", "microphone", False),
            ProviderTrackState("room_1", "publisher_2", "foreign_1", "microphone", True),
        )
        provider = FakeMediaProvider(tracks=states)
        lookup = MicrophoneTrackLookupRequest("room_1", "publisher_1", "microphone_1")

        verified = await provider.verify_microphone_track(lookup)

        assert verified == VerifiedMicrophoneTrack("room_1", "publisher_1", "microphone_1")
        denied = (
            MicrophoneTrackLookupRequest("room_2", "publisher_1", "microphone_1"),
            MicrophoneTrackLookupRequest("room_1", "publisher_1", "camera_1"),
            MicrophoneTrackLookupRequest("room_1", "publisher_1", "ended_1"),
            MicrophoneTrackLookupRequest("room_1", "publisher_1", "foreign_1"),
            MicrophoneTrackLookupRequest("room_1", "publisher_1", "unknown_1"),
        )
        for denied_lookup in denied:
            with pytest.raises(
                MediaProviderTrackVerificationError, match="active owned microphone"
            ):
                await provider.verify_microphone_track(denied_lookup)

    asyncio.run(exercise())


def test_selective_subscribe_and_unsubscribe_are_idempotent_and_exact() -> None:
    async def exercise() -> None:
        provider = FakeMediaProvider()
        track = VerifiedMicrophoneTrack("room_1", "publisher_1", "microphone_1")
        subscribe = SelectiveSubscriptionRequest(
            track=track,
            participant_refs=("listener_1", "listener_2"),
            action="subscribe",
        )
        unsubscribe = SelectiveSubscriptionRequest(
            track=track,
            participant_refs=("listener_1",),
            action="unsubscribe",
        )

        await provider.update_track_subscriptions(subscribe)
        await provider.update_track_subscriptions(subscribe)
        assert provider.subscriptions[("room_1", "microphone_1")] == frozenset(
            {"listener_1", "listener_2"}
        )

        await provider.update_track_subscriptions(unsubscribe)
        await provider.update_track_subscriptions(unsubscribe)
        assert provider.subscriptions[("room_1", "microphone_1")] == frozenset({"listener_2"})

    asyncio.run(exercise())


def test_injected_subscription_failure_is_atomic_and_cannot_broaden_delivery() -> None:
    async def exercise() -> None:
        provider = FakeMediaProvider(fail_subscription_calls=frozenset({2}))
        track = VerifiedMicrophoneTrack("room_1", "publisher_1", "microphone_1")
        first = SelectiveSubscriptionRequest(track, ("listener_1",), "subscribe")
        broaden = SelectiveSubscriptionRequest(track, ("listener_2", "listener_3"), "subscribe")

        await provider.update_track_subscriptions(first)
        with pytest.raises(MediaProviderSubscriptionError, match="synthetic"):
            await provider.update_track_subscriptions(broaden)

        assert provider.subscriptions[("room_1", "microphone_1")] == frozenset({"listener_1"})

    asyncio.run(exercise())


def test_subscription_request_rejects_ambiguous_recipient_sets() -> None:
    track = VerifiedMicrophoneTrack("room_1", "publisher_1", "microphone_1")
    with pytest.raises(ValueError, match="sorted and unique"):
        SelectiveSubscriptionRequest(track, ("listener_2", "listener_1"), "subscribe")
    with pytest.raises(ValueError, match="sorted and unique"):
        SelectiveSubscriptionRequest(track, ("listener_1", "listener_1"), "subscribe")
    with pytest.raises(TypeError, match="verified microphone"):
        SelectiveSubscriptionRequest(
            ProviderTrackState("room_1", "publisher_1", "camera_1", "camera", True),  # type: ignore[arg-type]
            ("listener_1",),
            "subscribe",
        )


def test_receive_request_cannot_enable_automatic_subscription() -> None:
    with pytest.raises(ValueError, match="must remain disabled"):
        ReceiveCredentialRequest(
            room_ref="room_1",
            participant_ref="participant_1",
            ttl_seconds=300,
            auto_subscribe=True,  # type: ignore[arg-type]
        )


def test_provider_factory_never_constructs_live_adapter() -> None:
    disabled = Settings(environment="test")
    assert isinstance(media_provider_from_settings(disabled), DisabledMediaProvider)

    enabled = Settings(
        environment="test",
        ptt_media_provider_enabled=True,
        ptt_media_provider="livekit",
        ptt_livekit_url="wss://synthetic.invalid",
        ptt_livekit_api_key=SecretStr("synthetic-key"),
        ptt_livekit_api_secret=SecretStr("synthetic-secret"),
    )
    with pytest.raises(MediaProviderUnavailableError, match="not implemented"):
        media_provider_from_settings(enabled)
