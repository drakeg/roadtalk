import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.ai.provider import AiProviderBoundary, DisabledAiProvider, FakeAiProvider
from app.ai.translation import (
    TRANSLATION_RESULT_MAX_CHARS,
    TRANSLATION_SOURCE_MAX_CHARS,
    AuthorizedTranslationSource,
    TranslationError,
    translate_authorized_text,
)


def source(now: datetime) -> AuthorizedTranslationSource:
    return AuthorizedTranslationSource(
        source_id=uuid.uuid4(),
        source_kind="transcript",
        text="Authorized conversation text.",
        source_language="en",
        observed_at=now,
        expires_at=now + timedelta(minutes=5),
    )


def test_translation_preserves_source_provenance_and_audience() -> None:
    now = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    value = source(now)
    request_id = uuid.uuid4()
    receipt = asyncio.run(
        translate_authorized_text(
            source=value,
            target_language="es",
            provider=AiProviderBoundary(
                FakeAiProvider(outputs={request_id: "Traducción determinista."})
            ),
            now=now + timedelta(seconds=1),
            request_id=request_id,
        )
    )

    assert receipt.request_id == request_id
    assert receipt.source_id == value.source_id
    assert receipt.source_kind == "transcript"
    assert receipt.translated_text == "Traducción determinista."
    assert receipt.source_language == "en"
    assert receipt.target_language == "es"
    assert receipt.state == "ready"
    assert receipt.provider_mode == "test"
    assert receipt.audience_preserved is True
    assert receipt.authorization_source == "existing_roadtalk_authorization"


def test_same_source_and_target_language_fails_before_provider_call() -> None:
    now = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    provider = FakeAiProvider()

    with pytest.raises(TranslationError) as error:
        asyncio.run(
            translate_authorized_text(
                source=source(now),
                target_language="en",
                provider=AiProviderBoundary(provider),
                now=now,
            )
        )

    assert error.value.code == "AI_TRANSLATION_LANGUAGE_INVALID"
    assert provider.text_requests == []


def test_stale_source_fails_closed_before_provider_call() -> None:
    now = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    value = AuthorizedTranslationSource(
        source_id=uuid.uuid4(),
        source_kind="message_window",
        text="Expired authorized text.",
        source_language="en",
        observed_at=now - timedelta(minutes=10),
        expires_at=now - timedelta(seconds=1),
    )
    provider = FakeAiProvider()

    with pytest.raises(TranslationError) as error:
        asyncio.run(
            translate_authorized_text(
                source=value,
                target_language="fr",
                provider=AiProviderBoundary(provider),
                now=now,
            )
        )

    assert error.value.code == "AI_TRANSLATION_SOURCE_STALE"
    assert provider.text_requests == []


def test_disabled_provider_is_normalized_to_generic_unavailable_error() -> None:
    now = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    with pytest.raises(TranslationError) as error:
        asyncio.run(
            translate_authorized_text(
                source=source(now),
                target_language="de",
                provider=AiProviderBoundary(DisabledAiProvider()),
                now=now,
            )
        )

    assert error.value.code == "AI_TRANSLATION_UNAVAILABLE"
    assert "provider" not in error.value.detail.lower()


def test_translation_source_is_closed_and_sensitive_overposting_is_rejected() -> None:
    now = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    value = source(now)

    for field in (
        "latitude",
        "longitude",
        "route_history",
        "audio",
        "recipient_ids",
        "nearby_users",
        "provider_key",
        "model",
        "prompt",
        "audience_override",
    ):
        with pytest.raises(ValidationError):
            AuthorizedTranslationSource.model_validate(
                {**value.model_dump(), field: "attacker-controlled"}
            )


def test_translation_source_and_result_bounds_are_enforced() -> None:
    now = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        AuthorizedTranslationSource(
            source_id=uuid.uuid4(),
            source_kind="transcript",
            text="x" * (TRANSLATION_SOURCE_MAX_CHARS + 1),
            source_language="en",
            observed_at=now,
            expires_at=now + timedelta(minutes=1),
        )

    with pytest.raises(TranslationError) as error:
        asyncio.run(
            translate_authorized_text(
                source=source(now),
                target_language="es",
                provider=AiProviderBoundary(FakeAiProvider()),
                max_output_chars=TRANSLATION_RESULT_MAX_CHARS + 1,
                now=now,
            )
        )
    assert error.value.code == "AI_TRANSLATION_BOUNDS_INVALID"


def test_provider_output_larger_than_requested_bound_is_rejected() -> None:
    now = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    request_id = uuid.uuid4()

    with pytest.raises(TranslationError) as error:
        asyncio.run(
            translate_authorized_text(
                source=source(now),
                target_language="fr",
                provider=AiProviderBoundary(FakeAiProvider(outputs={request_id: "x" * 101})),
                max_output_chars=100,
                now=now,
                request_id=request_id,
            )
        )

    assert error.value.code == "AI_TRANSLATION_OUTPUT_INVALID"


def test_source_timestamps_must_be_aware_and_ordered() -> None:
    naive = datetime(2026, 10, 3, 14, 0)
    with pytest.raises(ValidationError):
        AuthorizedTranslationSource(
            source_id=uuid.uuid4(),
            source_kind="transcript",
            text="Authorized text.",
            source_language="en",
            observed_at=naive,
            expires_at=naive + timedelta(minutes=1),
        )

    now = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    with pytest.raises(ValidationError):
        AuthorizedTranslationSource(
            source_id=uuid.uuid4(),
            source_kind="transcript",
            text="Authorized text.",
            source_language="en",
            observed_at=now,
            expires_at=now,
        )
