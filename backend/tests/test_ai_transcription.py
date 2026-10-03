import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.ai.contracts import ForegroundConsent
from app.ai.provider import (
    AI_PROVIDER_MAX_EPHEMERAL_AUDIO_BYTES,
    AiProviderBoundary,
    DisabledAiProvider,
    FakeAiProvider,
)
from app.ai.transcription import TranscriptionError, transcribe_foreground_audio


class FakeDb:
    def __init__(self, grant: object | None) -> None:
        self.grant = grant
        self.scalar_calls = 0

    async def scalar(self, statement: object) -> object | None:
        del statement
        self.scalar_calls += 1
        return self.grant


def active_grant(now: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        grant_kind="transmit",
        action_scope="microphone_publish",
        revoked_at=None,
        expires_at=now + timedelta(minutes=1),
    )


def test_transcription_requires_active_existing_transmit_authorization() -> None:
    now = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    grant = active_grant(now)
    db = FakeDb(grant)
    provider = FakeAiProvider()
    request_id = uuid.uuid4()

    receipt = asyncio.run(
        transcribe_foreground_audio(
            db,  # type: ignore[arg-type]
            account_id=grant.account_id,
            device_id=grant.device_id,
            transmit_grant_id=grant.id,
            language="en",
            consent=ForegroundConsent(),
            ephemeral_audio=b"synthetic-audio",
            provider=AiProviderBoundary(provider),
            now=now,
            request_id=request_id,
        )
    )

    assert receipt.request_id == request_id
    assert receipt.transmit_grant_id == grant.id
    assert receipt.transcript == "deterministic test transcript"
    assert receipt.provider_mode == "test"
    assert receipt.durable_audio_retention is False
    assert receipt.background_capture is False
    assert db.scalar_calls == 1


def test_transcription_fails_closed_without_active_transmit_grant() -> None:
    now = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    with pytest.raises(TranscriptionError) as error:
        asyncio.run(
            transcribe_foreground_audio(
                FakeDb(None),  # type: ignore[arg-type]
                account_id=uuid.uuid4(),
                device_id=uuid.uuid4(),
                transmit_grant_id=uuid.uuid4(),
                language="en",
                consent=ForegroundConsent(),
                ephemeral_audio=b"synthetic-audio",
                provider=AiProviderBoundary(FakeAiProvider()),
                now=now,
            )
        )
    assert error.value.code == "AI_TRANSCRIPTION_NOT_AUTHORIZED"


def test_disabled_provider_is_normalized_to_generic_unavailable_error() -> None:
    now = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    grant = active_grant(now)

    with pytest.raises(TranscriptionError) as error:
        asyncio.run(
            transcribe_foreground_audio(
                FakeDb(grant),  # type: ignore[arg-type]
                account_id=grant.account_id,
                device_id=grant.device_id,
                transmit_grant_id=grant.id,
                language="en",
                consent=ForegroundConsent(),
                ephemeral_audio=b"synthetic-audio",
                provider=AiProviderBoundary(DisabledAiProvider()),
                now=now,
            )
        )
    assert error.value.code == "AI_TRANSCRIPTION_UNAVAILABLE"
    assert "provider" not in error.value.detail.lower()


def test_audio_is_only_passed_to_provider_and_not_returned_or_persisted() -> None:
    now = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    grant = active_grant(now)
    provider = FakeAiProvider()

    receipt = asyncio.run(
        transcribe_foreground_audio(
            FakeDb(grant),  # type: ignore[arg-type]
            account_id=grant.account_id,
            device_id=grant.device_id,
            transmit_grant_id=grant.id,
            language="en",
            consent=ForegroundConsent(),
            ephemeral_audio=b"ephemeral-only",
            provider=AiProviderBoundary(provider),
            now=now,
        )
    )

    assert not hasattr(receipt, "audio")
    assert not hasattr(receipt, "ephemeral_audio")
    assert len(provider.transcription_requests) == 1
    assert provider.transcription_requests[0].ephemeral_audio == b"ephemeral-only"


def test_ephemeral_audio_bound_is_enforced_before_provider_processing() -> None:
    now = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    grant = active_grant(now)

    with pytest.raises(ValidationError):
        asyncio.run(
            transcribe_foreground_audio(
                FakeDb(grant),  # type: ignore[arg-type]
                account_id=grant.account_id,
                device_id=grant.device_id,
                transmit_grant_id=grant.id,
                language="en",
                consent=ForegroundConsent(),
                ephemeral_audio=b"x" * (AI_PROVIDER_MAX_EPHEMERAL_AUDIO_BYTES + 1),
                provider=AiProviderBoundary(FakeAiProvider()),
                now=now,
            )
        )
