from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import NoReturn, Protocol

from pydantic import SecretStr

from app.config import Settings


class MediaProviderError(RuntimeError):
    """Stable base error that never contains provider payloads or credentials."""


class MediaProviderDisabledError(MediaProviderError):
    """Raised when media operations are attempted while the provider is disabled."""


class MediaProviderUnavailableError(MediaProviderError):
    """Raised when an approved production adapter is not installed or available."""


@dataclass(frozen=True, slots=True)
class ReceiveCredentialRequest:
    room_ref: str
    participant_ref: str
    ttl_seconds: int


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
class ReceiveCredential:
    server_url: str
    participant_token: SecretStr
    expires_at: datetime


class MediaProvider(Protocol):
    async def issue_receive_credential(
        self, request: ReceiveCredentialRequest
    ) -> ReceiveCredential: ...

    async def set_microphone_publish(
        self, request: MicrophonePublishRequest
    ) -> None: ...

    async def remove_participant(self, request: ParticipantRequest) -> None: ...


class DisabledMediaProvider:
    def _raise(self) -> NoReturn:
        raise MediaProviderDisabledError("PTT media provider is disabled")

    async def issue_receive_credential(
        self, request: ReceiveCredentialRequest
    ) -> ReceiveCredential:
        del request
        self._raise()

    async def set_microphone_publish(
        self, request: MicrophonePublishRequest
    ) -> None:
        del request
        self._raise()

    async def remove_participant(self, request: ParticipantRequest) -> None:
        del request
        self._raise()


class FakeMediaProvider:
    """Deterministic, no-network provider for unit tests and CI."""

    def __init__(
        self,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._now = now or (lambda: datetime.now(UTC))
        self.receive_requests: list[ReceiveCredentialRequest] = []
        self.publish_requests: list[MicrophonePublishRequest] = []
        self.remove_requests: list[ParticipantRequest] = []

    async def issue_receive_credential(
        self, request: ReceiveCredentialRequest
    ) -> ReceiveCredential:
        self.receive_requests.append(request)
        return ReceiveCredential(
            server_url="wss://synthetic.invalid",
            participant_token=SecretStr(
                f"synthetic-provider-token::{request.participant_ref}"
            ),
            expires_at=self._now() + timedelta(seconds=request.ttl_seconds),
        )

    async def set_microphone_publish(
        self, request: MicrophonePublishRequest
    ) -> None:
        self.publish_requests.append(request)

    async def remove_participant(self, request: ParticipantRequest) -> None:
        self.remove_requests.append(request)


def media_provider_from_settings(settings: Settings) -> MediaProvider:
    if not settings.ptt_media_provider_enabled:
        return DisabledMediaProvider()
    raise MediaProviderUnavailableError(
        "live PTT media adapter is not implemented in S04-D02"
    )
