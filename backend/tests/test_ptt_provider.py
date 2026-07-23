import asyncio
from datetime import UTC, datetime

import pytest
from pydantic import SecretStr

from app.config import Settings
from app.ptt.provider import (
    DisabledMediaProvider,
    FakeMediaProvider,
    MediaProviderDisabledError,
    MediaProviderUnavailableError,
    MicrophonePublishRequest,
    ParticipantRequest,
    ReceiveCredentialRequest,
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
        assert "synthetic-provider-token" not in repr(credential)

    asyncio.run(exercise())


def test_provider_factory_never_constructs_live_adapter_in_d02() -> None:
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
