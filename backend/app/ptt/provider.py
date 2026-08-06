from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, NoReturn, Protocol

import jwt
from pydantic import SecretStr

from app.config import Settings


class MediaProviderError(RuntimeError):
    """Stable base error that never contains provider payloads or credentials."""


class MediaProviderDisabledError(MediaProviderError):
    """Raised when media operations are attempted while the provider is disabled."""


class MediaProviderUnavailableError(MediaProviderError):
    """Raised when an approved production adapter is not installed or available."""


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
    raise MediaProviderUnavailableError("live PTT media adapter is not implemented")
