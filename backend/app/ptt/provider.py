from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, NoReturn, Protocol

import jwt
from livekit import api
from pydantic import SecretStr

from app.config import Settings


class MediaProviderError(RuntimeError):
    """Stable base error that never contains provider payloads or credentials."""


class MediaProviderDisabledError(MediaProviderError):
    """Raised when media operations are attempted while the provider is disabled."""


class MediaProviderUnavailableError(MediaProviderError):
    """Raised when the configured media provider is unavailable."""


class MediaProviderTrackVerificationError(MediaProviderError):
    """Raised when an opaque track cannot be verified as an active owned microphone."""


class MediaProviderSubscriptionError(MediaProviderError):
    """Raised when a selective-subscription request fails before safe application."""


@dataclass(frozen=True, slots=True)
class ReceiveCredentialRequest:
    room_ref: str
    participant_ref: str
    ttl_seconds: int
    auto_subscribe: Literal[False] = False

    def __post_init__(self) -> None:
        if self.auto_subscribe is not False:
            raise ValueError("automatic media subscription must remain disabled")


@dataclass(frozen=True, slots=True)
class MicrophonePublishRequest:
    room_ref: str
    participant_ref: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class ParticipantRequest:
    room_ref: str
    participant_ref: str


@dataclass(frozen=True, slots=True)
class MicrophoneTrackLookupRequest:
    room_ref: str
    participant_ref: str
    track_ref: str


@dataclass(frozen=True, slots=True)
class ProviderTrackState:
    """Synthetic provider observation used only by the deterministic fake."""

    room_ref: str
    participant_ref: str
    track_ref: str
    source: str
    active: bool


@dataclass(frozen=True, slots=True)
class VerifiedMicrophoneTrack:
    room_ref: str
    participant_ref: str
    track_ref: str
    source: Literal["microphone"] = "microphone"
    active: Literal[True] = True

    def __post_init__(self) -> None:
        if self.source != "microphone" or self.active is not True:
            raise ValueError("verified track must be an active microphone publication")


@dataclass(frozen=True, slots=True)
class SelectiveSubscriptionRequest:
    track: VerifiedMicrophoneTrack
    participant_refs: tuple[str, ...]
    action: Literal["subscribe", "unsubscribe"]

    def __post_init__(self) -> None:
        if not isinstance(self.track, VerifiedMicrophoneTrack):
            raise TypeError("selective subscription requires a verified microphone track")
        if not self.participant_refs:
            raise ValueError("selective subscription requires at least one participant")
        if any(not participant_ref for participant_ref in self.participant_refs):
            raise ValueError("participant references must be opaque non-empty values")
        if self.participant_refs != tuple(sorted(set(self.participant_refs))):
            raise ValueError("participant references must be sorted and unique")


@dataclass(frozen=True, slots=True)
class ReceiveCredential:
    server_url: str
    participant_token: SecretStr
    expires_at: datetime


class MediaProvider(Protocol):
    async def issue_receive_credential(
        self, request: ReceiveCredentialRequest
    ) -> ReceiveCredential: ...

    async def set_microphone_publish(self, request: MicrophonePublishRequest) -> None: ...

    async def remove_participant(self, request: ParticipantRequest) -> None: ...

    async def verify_microphone_track(
        self, request: MicrophoneTrackLookupRequest
    ) -> VerifiedMicrophoneTrack: ...

    async def update_track_subscriptions(self, request: SelectiveSubscriptionRequest) -> None: ...


class DisabledMediaProvider:
    def _raise(self) -> NoReturn:
        raise MediaProviderDisabledError("PTT media provider is disabled")

    async def issue_receive_credential(
        self, request: ReceiveCredentialRequest
    ) -> ReceiveCredential:
        del request
        self._raise()

    async def set_microphone_publish(self, request: MicrophonePublishRequest) -> None:
        del request
        self._raise()

    async def remove_participant(self, request: ParticipantRequest) -> None:
        del request
        self._raise()

    async def verify_microphone_track(
        self, request: MicrophoneTrackLookupRequest
    ) -> VerifiedMicrophoneTrack:
        del request
        self._raise()

    async def update_track_subscriptions(self, request: SelectiveSubscriptionRequest) -> None:
        del request
        self._raise()


class LiveKitMediaProvider:
    """LiveKit adapter used by local self-hosted and approved live deployments."""

    _MICROPHONE_SOURCE = 2

    def __init__(
        self,
        *,
        server_url: str,
        api_url: str,
        api_key: str,
        api_secret: str,
    ) -> None:
        self._server_url = server_url
        self._api_url = api_url
        self._api_key = api_key
        self._api_secret = api_secret

    def _client(self) -> api.LiveKitAPI:
        return api.LiveKitAPI(
            url=self._api_url,
            api_key=self._api_key,
            api_secret=self._api_secret,
        )

    async def issue_receive_credential(
        self, request: ReceiveCredentialRequest
    ) -> ReceiveCredential:
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=request.ttl_seconds)
        token = (
            api.AccessToken(self._api_key, self._api_secret)
            .with_identity(request.participant_ref)
            .with_ttl(timedelta(seconds=request.ttl_seconds))
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=request.room_ref,
                    can_subscribe=True,
                    can_publish=False,
                    can_publish_data=False,
                )
            )
            .to_jwt()
        )
        return ReceiveCredential(
            server_url=self._server_url,
            participant_token=SecretStr(token),
            expires_at=expires_at,
        )

    async def set_microphone_publish(self, request: MicrophonePublishRequest) -> None:
        permission = api.ParticipantPermission(
            can_subscribe=True,
            can_publish=request.enabled,
            can_publish_data=False,
            can_publish_sources=(
                [self._MICROPHONE_SOURCE] if request.enabled else []
            ),
        )
        try:
            async with self._client() as client:
                await client.room.update_participant(
                    api.UpdateParticipantRequest(
                        room=request.room_ref,
                        identity=request.participant_ref,
                        permission=permission,
                    )
                )
        except Exception as exc:
            raise MediaProviderUnavailableError(
                "LiveKit participant permission update failed"
            ) from exc

    async def remove_participant(self, request: ParticipantRequest) -> None:
        try:
            async with self._client() as client:
                await client.room.remove_participant(
                    api.RoomParticipantIdentity(
                        room=request.room_ref,
                        identity=request.participant_ref,
                    )
                )
        except Exception as exc:
            raise MediaProviderUnavailableError("LiveKit participant removal failed") from exc

    async def verify_microphone_track(
        self, request: MicrophoneTrackLookupRequest
    ) -> VerifiedMicrophoneTrack:
        try:
            async with self._client() as client:
                participant = await client.room.get_participant(
                    api.RoomParticipantIdentity(
                        room=request.room_ref,
                        identity=request.participant_ref,
                    )
                )
        except Exception as exc:
            raise MediaProviderTrackVerificationError(
                "LiveKit participant lookup failed"
            ) from exc

        observed = next(
            (track for track in participant.tracks if track.sid == request.track_ref),
            None,
        )
        if (
            observed is None
            or int(observed.source) != self._MICROPHONE_SOURCE
            or observed.muted
        ):
            raise MediaProviderTrackVerificationError(
                "opaque track is not an active owned microphone publication"
            )
        return VerifiedMicrophoneTrack(
            room_ref=request.room_ref,
            participant_ref=request.participant_ref,
            track_ref=request.track_ref,
        )

    async def update_track_subscriptions(self, request: SelectiveSubscriptionRequest) -> None:
        try:
            async with self._client() as client:
                for participant_ref in request.participant_refs:
                    await client.room.update_subscriptions(
                        api.UpdateSubscriptionsRequest(
                            room=request.track.room_ref,
                            identity=participant_ref,
                            track_sids=[request.track.track_ref],
                            subscribe=request.action == "subscribe",
                        )
                    )
        except Exception as exc:
            raise MediaProviderSubscriptionError(
                "LiveKit selective subscription update failed"
            ) from exc


class FakeMediaProvider:
    """Deterministic, no-network provider for unit tests and CI."""

    def __init__(
        self,
        *,
        now: Callable[[], datetime] | None = None,
        tracks: tuple[ProviderTrackState, ...] = (),
        fail_subscription_calls: frozenset[int] = frozenset(),
    ) -> None:
        self._now = now or (lambda: datetime.now(UTC))
        self._tracks = {track.track_ref: track for track in tracks}
        self._fail_subscription_calls = fail_subscription_calls
        self._subscription_call_count = 0
        self.receive_requests: list[ReceiveCredentialRequest] = []
        self.publish_requests: list[MicrophonePublishRequest] = []
        self.remove_requests: list[ParticipantRequest] = []
        self.track_lookup_requests: list[MicrophoneTrackLookupRequest] = []
        self.subscription_requests: list[SelectiveSubscriptionRequest] = []
        self.subscriptions: dict[tuple[str, str], frozenset[str]] = {}

    async def issue_receive_credential(
        self, request: ReceiveCredentialRequest
    ) -> ReceiveCredential:
        self.receive_requests.append(request)
        issued_at = self._now()
        expires_at = issued_at + timedelta(seconds=request.ttl_seconds)
        token = jwt.encode(
            {
                "iss": "synthetic-livekit-key",
                "sub": request.participant_ref,
                "nbf": int(issued_at.timestamp()),
                "exp": int(expires_at.timestamp()),
                "video": {
                    "room": request.room_ref,
                    "roomJoin": True,
                    "canSubscribe": True,
                    "canPublish": False,
                    "canPublishData": False,
                    "roomAdmin": False,
                    "recorder": False,
                },
            },
            "synthetic-livekit-secret-for-tests-only",
            algorithm="HS256",
        )
        return ReceiveCredential(
            server_url="wss://synthetic.invalid",
            participant_token=SecretStr(token),
            expires_at=expires_at,
        )

    async def set_microphone_publish(self, request: MicrophonePublishRequest) -> None:
        self.publish_requests.append(request)

    async def remove_participant(self, request: ParticipantRequest) -> None:
        self.remove_requests.append(request)

    async def verify_microphone_track(
        self, request: MicrophoneTrackLookupRequest
    ) -> VerifiedMicrophoneTrack:
        self.track_lookup_requests.append(request)
        observed = self._tracks.get(request.track_ref)
        if (
            observed is None
            or observed.room_ref != request.room_ref
            or observed.participant_ref != request.participant_ref
            or observed.source != "microphone"
            or not observed.active
        ):
            raise MediaProviderTrackVerificationError(
                "opaque track is not an active owned microphone publication"
            )
        return VerifiedMicrophoneTrack(
            room_ref=observed.room_ref,
            participant_ref=observed.participant_ref,
            track_ref=observed.track_ref,
        )

    async def update_track_subscriptions(self, request: SelectiveSubscriptionRequest) -> None:
        self.subscription_requests.append(request)
        self._subscription_call_count += 1
        if self._subscription_call_count in self._fail_subscription_calls:
            raise MediaProviderSubscriptionError("synthetic selective-subscription failure")

        key = (request.track.room_ref, request.track.track_ref)
        current = set(self.subscriptions.get(key, frozenset()))
        if request.action == "subscribe":
            current.update(request.participant_refs)
        else:
            current.difference_update(request.participant_refs)
        self.subscriptions[key] = frozenset(current)


def media_provider_from_settings(settings: Settings) -> MediaProvider:
    if not settings.ptt_media_provider_enabled:
        return DisabledMediaProvider()
    if settings.ptt_media_provider != "livekit":
        raise MediaProviderUnavailableError("unsupported PTT media provider")
    if (
        settings.ptt_livekit_url is None
        or settings.ptt_livekit_api_url is None
        or settings.ptt_livekit_api_key is None
        or settings.ptt_livekit_api_secret is None
    ):
        raise MediaProviderUnavailableError("LiveKit media configuration is incomplete")
    return LiveKitMediaProvider(
        server_url=settings.ptt_livekit_url,
        api_url=settings.ptt_livekit_api_url,
        api_key=settings.ptt_livekit_api_key.get_secret_value(),
        api_secret=settings.ptt_livekit_api_secret.get_secret_value(),
    )
