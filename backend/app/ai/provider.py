from __future__ import annotations

import asyncio
import uuid
from collections import deque
from collections.abc import Awaitable, Mapping
from enum import StrEnum
from threading import Lock
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.ai.contracts import SupportedLanguage

AI_PROVIDER_TIMEOUT_MS = 500
AI_PROVIDER_MAX_TEXT_CHARS = 8_000
AI_PROVIDER_MAX_EPHEMERAL_AUDIO_BYTES = 262_144
AI_PROVIDER_MAX_CONCURRENT_REQUESTS = 4
AI_PROVIDER_REPLAY_WINDOW = 256


class AiProviderMode(StrEnum):
    DISABLED = "disabled"
    TEST = "test"


class AiProviderCapability(StrEnum):
    TRANSCRIPTION = "transcription"
    SUMMARY = "summary"
    TRANSLATION = "translation"


class AiProviderHealth(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: AiProviderMode
    available: bool
    capabilities: tuple[AiProviderCapability, ...] = ()


class AiTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: uuid.UUID
    capability: Literal["summary", "translation"]
    input_text: str = Field(min_length=1, max_length=AI_PROVIDER_MAX_TEXT_CHARS)
    source_language: SupportedLanguage
    target_language: SupportedLanguage | None = None

    @model_validator(mode="after")
    def translation_language_contract(self) -> AiTextRequest:
        if self.capability == "translation":
            if self.target_language is None:
                raise ValueError("translation requires a target language")
            if self.target_language == self.source_language:
                raise ValueError("translation target must differ from source")
        elif self.target_language is not None:
            raise ValueError("summary requests cannot set a target language")
        return self


class AiTranscriptionRequest(BaseModel):
    """Server-internal ephemeral transcription request; never a persistence schema."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: uuid.UUID
    language: SupportedLanguage
    ephemeral_audio: bytes = Field(
        min_length=1,
        max_length=AI_PROVIDER_MAX_EPHEMERAL_AUDIO_BYTES,
    )


class AiProviderResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: uuid.UUID
    capability: AiProviderCapability
    output_text: str = Field(min_length=1, max_length=AI_PROVIDER_MAX_TEXT_CHARS)
    provider_mode: Literal["test"] = "test"
    provider_version: Literal["test-v1"] = "test-v1"


class AiProviderError(RuntimeError):
    """Stable non-disclosing AI provider failure."""


class AiProviderUnavailable(AiProviderError):
    """Configured provider is disabled or failed closed."""


class AiProvider(Protocol):
    def health(self) -> AiProviderHealth: ...

    async def process_text(self, request: AiTextRequest) -> AiProviderResult: ...

    async def transcribe(self, request: AiTranscriptionRequest) -> AiProviderResult: ...


class DisabledAiProvider:
    def health(self) -> AiProviderHealth:
        return AiProviderHealth(mode=AiProviderMode.DISABLED, available=False)

    async def process_text(self, request: AiTextRequest) -> AiProviderResult:
        del request
        raise AiProviderUnavailable("AI provider unavailable")

    async def transcribe(self, request: AiTranscriptionRequest) -> AiProviderResult:
        del request
        raise AiProviderUnavailable("AI provider unavailable")


class FakeAiProvider:
    """Deterministic local/CI provider with no network or external model dependency."""

    def __init__(
        self,
        *,
        outputs: Mapping[uuid.UUID, str] | None = None,
    ) -> None:
        self._outputs = dict(outputs or {})
        self.text_requests: list[AiTextRequest] = []
        self.transcription_requests: list[AiTranscriptionRequest] = []

    def health(self) -> AiProviderHealth:
        return AiProviderHealth(
            mode=AiProviderMode.TEST,
            available=True,
            capabilities=(
                AiProviderCapability.TRANSCRIPTION,
                AiProviderCapability.SUMMARY,
                AiProviderCapability.TRANSLATION,
            ),
        )

    async def process_text(self, request: AiTextRequest) -> AiProviderResult:
        self.text_requests.append(request)
        output = self._outputs.get(
            request.request_id,
            (
                "deterministic test summary"
                if request.capability == "summary"
                else f"deterministic test translation ({request.target_language})"
            ),
        )
        return AiProviderResult(
            request_id=request.request_id,
            capability=AiProviderCapability(request.capability),
            output_text=output,
        )

    async def transcribe(self, request: AiTranscriptionRequest) -> AiProviderResult:
        self.transcription_requests.append(request)
        output = self._outputs.get(request.request_id, "deterministic test transcript")
        return AiProviderResult(
            request_id=request.request_id,
            capability=AiProviderCapability.TRANSCRIPTION,
            output_text=output,
        )


class AiProviderBoundary:
    """Timeout and integrity boundary around the configured AI provider."""

    def __init__(
        self,
        provider: AiProvider,
        *,
        timeout_ms: int = AI_PROVIDER_TIMEOUT_MS,
        max_concurrent_requests: int = AI_PROVIDER_MAX_CONCURRENT_REQUESTS,
        replay_window: int = AI_PROVIDER_REPLAY_WINDOW,
    ) -> None:
        if not 10 <= timeout_ms <= 2_000:
            raise ValueError("AI provider timeout is out of bounds")
        if not 1 <= max_concurrent_requests <= 32:
            raise ValueError("AI provider concurrency limit is out of bounds")
        if not 1 <= replay_window <= 1_024:
            raise ValueError("AI provider replay window is out of bounds")
        self._provider = provider
        self._timeout_seconds = timeout_ms / 1_000
        self._max_concurrent_requests = max_concurrent_requests
        self._replay_window = replay_window
        self._request_lock = Lock()
        self._active_request_ids: set[uuid.UUID] = set()
        self._completed_request_ids: set[uuid.UUID] = set()
        self._completed_request_order: deque[uuid.UUID] = deque()

    def health(self) -> AiProviderHealth:
        try:
            health = self._provider.health()
        except Exception:
            return AiProviderHealth(mode=AiProviderMode.DISABLED, available=False)
        if health.mode not in {AiProviderMode.DISABLED, AiProviderMode.TEST}:
            return AiProviderHealth(mode=AiProviderMode.DISABLED, available=False)
        return health

    async def process_text(self, request: AiTextRequest) -> AiProviderResult:
        self._claim_request(request.request_id)
        try:
            return await self._run(
                request_id=request.request_id,
                capability=AiProviderCapability(request.capability),
                operation=self._provider.process_text(request),
            )
        finally:
            self._finish_request(request.request_id)

    async def transcribe(self, request: AiTranscriptionRequest) -> AiProviderResult:
        self._claim_request(request.request_id)
        try:
            return await self._run(
                request_id=request.request_id,
                capability=AiProviderCapability.TRANSCRIPTION,
                operation=self._provider.transcribe(request),
            )
        finally:
            self._finish_request(request.request_id)

    async def _run(
        self,
        *,
        request_id: uuid.UUID,
        capability: AiProviderCapability,
        operation: Awaitable[AiProviderResult],
    ) -> AiProviderResult:
        try:
            result = await asyncio.wait_for(operation, timeout=self._timeout_seconds)
        except Exception:
            raise AiProviderUnavailable("AI provider unavailable") from None

        if result.request_id != request_id or result.capability != capability:
            raise AiProviderUnavailable("AI provider unavailable")
        if result.provider_mode != "test" or result.provider_version != "test-v1":
            raise AiProviderUnavailable("AI provider unavailable")
        return result

    def _claim_request(self, request_id: uuid.UUID) -> None:
        with self._request_lock:
            if (
                request_id in self._active_request_ids
                or request_id in self._completed_request_ids
                or len(self._active_request_ids) >= self._max_concurrent_requests
            ):
                raise AiProviderUnavailable("AI provider unavailable")
            self._active_request_ids.add(request_id)

    def _finish_request(self, request_id: uuid.UUID) -> None:
        with self._request_lock:
            self._active_request_ids.discard(request_id)
            if request_id in self._completed_request_ids:
                return
            if len(self._completed_request_order) >= self._replay_window:
                expired_request_id = self._completed_request_order.popleft()
                self._completed_request_ids.discard(expired_request_id)
            self._completed_request_order.append(request_id)
            self._completed_request_ids.add(request_id)


def build_ai_provider(
    provider: Literal["disabled", "fake"] = "disabled",
    *,
    environment: Literal["local", "test", "field-test", "production"] = "local",
    outputs: Mapping[uuid.UUID, str] | None = None,
) -> AiProvider:
    if environment not in {"local", "test"} and provider != "disabled":
        raise AiProviderUnavailable("AI provider unavailable")
    if provider == "disabled":
        return DisabledAiProvider()
    if provider == "fake":
        return FakeAiProvider(outputs=outputs)
    raise AiProviderUnavailable("AI provider unavailable")
