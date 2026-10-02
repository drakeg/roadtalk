import uuid

import pytest
from pydantic import ValidationError

from app.ai.contracts import (
    PROHIBITED_AI_FIELDS,
    AiResultContext,
    AuthorizedTextSource,
    ForegroundConsent,
    SummaryCommand,
    TranscriptionIntent,
    TranslationCommand,
)


def source() -> AuthorizedTextSource:
    return AuthorizedTextSource(
        source_id=uuid.uuid4(),
        source_kind="transcript",
    )


def test_transcription_intent_requires_explicit_foreground_nonretaining_consent() -> None:
    intent = TranscriptionIntent(
        session_id=uuid.uuid4(),
        language="en",
        consent=ForegroundConsent(),
    )
    assert intent.consent.user_initiated is True
    assert intent.consent.foreground_only is True
    assert intent.consent.background_capture is False
    assert intent.consent.durable_audio_retention is False

    for field, value in (
        ("user_initiated", False),
        ("foreground_only", False),
        ("background_capture", True),
        ("durable_audio_retention", True),
    ):
        with pytest.raises(ValidationError):
            ForegroundConsent.model_validate({**ForegroundConsent().model_dump(), field: value})


def test_ai_commands_are_closed_and_reject_sensitive_overposting() -> None:
    summary = SummaryCommand(source=source())
    translation = TranslationCommand(
        source=source(),
        source_language="en",
        target_language="es",
    )
    intent = TranscriptionIntent(
        session_id=uuid.uuid4(),
        language="en",
        consent=ForegroundConsent(),
    )

    for command in (summary, translation, intent):
        for forbidden in sorted(PROHIBITED_AI_FIELDS):
            with pytest.raises(ValidationError):
                command.__class__.model_validate(
                    {**command.model_dump(), forbidden: "attacker-controlled"}
                )


def test_authorized_source_is_restrictive_only_and_cannot_override_authorization() -> None:
    value = source()
    assert value.authorized_only is True
    assert value.authorization_source == "existing_roadtalk_authorization"

    with pytest.raises(ValidationError):
        AuthorizedTextSource.model_validate({**value.model_dump(), "authorized_only": False})
    with pytest.raises(ValidationError):
        AuthorizedTextSource.model_validate({**value.model_dump(), "authorization_source": "ai"})


@pytest.mark.parametrize("language", ["en", "es", "fr", "de"])
def test_supported_languages_are_bounded(language: str) -> None:
    TranscriptionIntent(
        session_id=uuid.uuid4(),
        language=language,
        consent=ForegroundConsent(),
    )

    with pytest.raises(ValidationError):
        TranscriptionIntent(
            session_id=uuid.uuid4(),
            language="unsupported",
            consent=ForegroundConsent(),
        )


def test_translation_requires_distinct_bounded_languages() -> None:
    TranslationCommand(
        source=source(),
        source_language="en",
        target_language="de",
    )
    with pytest.raises(ValidationError):
        TranslationCommand(
            source=source(),
            source_language="en",
            target_language="en",
        )
    with pytest.raises(ValidationError):
        TranslationCommand(
            source=source(),
            source_language="en",
            target_language="ja",
        )


def test_output_size_is_bounded() -> None:
    with pytest.raises(ValidationError):
        SummaryCommand(source=source(), max_output_chars=4001)
    with pytest.raises(ValidationError):
        TranslationCommand(
            source=source(),
            source_language="en",
            target_language="es",
            max_output_chars=8001,
        )


def test_ai_result_context_cannot_claim_live_provider_or_audio_retention() -> None:
    context = AiResultContext(
        capability="summary",
        state="ready",
        source_id=uuid.uuid4(),
        source_kind="message_window",
        provider_mode="test",
    )
    assert context.authorization_source == "existing_roadtalk_authorization"
    assert context.durable_audio_retention is False
    assert context.background_capture is False

    with pytest.raises(ValidationError):
        AiResultContext.model_validate({**context.model_dump(), "provider_mode": "live"})
    with pytest.raises(ValidationError):
        AiResultContext.model_validate({**context.model_dump(), "durable_audio_retention": True})
