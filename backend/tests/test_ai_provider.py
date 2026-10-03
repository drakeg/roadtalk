import asyncio
import uuid

import pytest
from pydantic import ValidationError

from app.ai.provider import (
    AI_PROVIDER_MAX_EPHEMERAL_AUDIO_BYTES,
    AiProviderBoundary,
    AiProviderCapability,
    AiProviderHealth,
    AiProviderMode,
    AiProviderResult,
    AiProviderUnavailable,
    AiTextRequest,
    AiTranscriptionRequest,
    DisabledAiProvider,
    FakeAiProvider,
    build_ai_provider,
)


def test_disabled_provider_reports_unavailable_and_fails_closed() -> None:
    provider = DisabledAiProvider()
    assert provider.health() == AiProviderHealth(
        mode=AiProviderMode.DISABLED,
        available=False,
    )

    with pytest.raises(AiProviderUnavailable, match="AI provider unavailable"):
        asyncio.run(
            provider.process_text(
                AiTextRequest(
                    request_id=uuid.uuid4(),
                    capability="summary",
                    input_text="authorized bounded text",
                    source_language="en",
                )
            )
        )


def test_fake_provider_is_deterministic_and_no_network_metadata_is_exposed() -> None:
    request_id = uuid.uuid4()
    provider = FakeAiProvider(outputs={request_id: "bounded result"})
    result = asyncio.run(
        provider.process_text(
            AiTextRequest(
                request_id=request_id,
                capability="summary",
                input_text="authorized bounded text",
                source_language="en",
            )
        )
    )

    assert result == AiProviderResult(
        request_id=request_id,
        capability=AiProviderCapability.SUMMARY,
        output_text="bounded result",
    )
    assert provider.health().mode == AiProviderMode.TEST
    assert set(result.model_dump()) == {
        "request_id",
        "capability",
        "output_text",
        "provider_mode",
        "provider_version",
    }


def test_text_request_language_contract_is_bounded() -> None:
    AiTextRequest(
        request_id=uuid.uuid4(),
        capability="translation",
        input_text="hello",
        source_language="en",
        target_language="es",
    )

    with pytest.raises(ValidationError):
        AiTextRequest(
            request_id=uuid.uuid4(),
            capability="translation",
            input_text="hello",
            source_language="en",
        )
    with pytest.raises(ValidationError):
        AiTextRequest(
            request_id=uuid.uuid4(),
            capability="summary",
            input_text="hello",
            source_language="en",
            target_language="es",
        )


def test_transcription_request_is_ephemeral_bounded_and_closed() -> None:
    request = AiTranscriptionRequest(
        request_id=uuid.uuid4(),
        language="en",
        ephemeral_audio=b"synthetic-test-bytes",
    )
    assert set(request.model_dump()) == {"request_id", "language", "ephemeral_audio"}

    with pytest.raises(ValidationError):
        AiTranscriptionRequest(
            request_id=uuid.uuid4(),
            language="en",
            ephemeral_audio=b"x" * (AI_PROVIDER_MAX_EPHEMERAL_AUDIO_BYTES + 1),
        )
    with pytest.raises(ValidationError):
        AiTranscriptionRequest.model_validate(
            {
                **request.model_dump(),
                "audio_url": "https://provider.invalid/recording",
            }
        )


def test_boundary_rejects_mismatched_or_disclosing_provider_results() -> None:
    request = AiTextRequest(
        request_id=uuid.uuid4(),
        capability="summary",
        input_text="authorized bounded text",
        source_language="en",
    )

    class MismatchedProvider(FakeAiProvider):
        async def process_text(self, value: AiTextRequest) -> AiProviderResult:
            return AiProviderResult(
                request_id=uuid.uuid4(),
                capability=AiProviderCapability.SUMMARY,
                output_text="wrong request",
            )

    boundary = AiProviderBoundary(MismatchedProvider())
    with pytest.raises(AiProviderUnavailable, match="AI provider unavailable"):
        asyncio.run(boundary.process_text(request))


def test_boundary_normalizes_provider_exceptions() -> None:
    request = AiTextRequest(
        request_id=uuid.uuid4(),
        capability="summary",
        input_text="authorized bounded text",
        source_language="en",
    )

    class BrokenProvider(FakeAiProvider):
        async def process_text(self, value: AiTextRequest) -> AiProviderResult:
            del value
            raise RuntimeError("provider-secret-detail")

    with pytest.raises(AiProviderUnavailable) as error:
        asyncio.run(AiProviderBoundary(BrokenProvider()).process_text(request))
    assert "provider-secret-detail" not in str(error.value)


def test_builder_allows_fake_only_in_local_or_test_environments() -> None:
    assert isinstance(build_ai_provider(), DisabledAiProvider)
    assert isinstance(build_ai_provider("fake", environment="test"), FakeAiProvider)

    with pytest.raises(AiProviderUnavailable, match="AI provider unavailable"):
        build_ai_provider("fake", environment="production")


def test_no_live_provider_configuration_is_exposed_by_contract() -> None:
    provider_fields = set(AiProviderResult.model_fields)
    request_fields = set(AiTextRequest.model_fields) | set(AiTranscriptionRequest.model_fields)
    forbidden = {
        "api_key",
        "provider_url",
        "model",
        "model_id",
        "credential",
        "token",
        "access_token",
        "refresh_token",
    }
    assert provider_fields.isdisjoint(forbidden)
    assert request_fields.isdisjoint(forbidden)
