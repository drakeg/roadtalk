from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.contracts import ForegroundConsent, SupportedLanguage
from app.ai.provider import (
    AiProviderBoundary,
    AiProviderUnavailable,
    AiTranscriptionRequest,
)
from app.db.models import MediaGrant


class TranscriptionError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class TranscriptionReceipt:
    request_id: uuid.UUID
    transmit_grant_id: uuid.UUID
    transcript: str
    language: SupportedLanguage
    provider_mode: str
    completed_at: datetime
    durable_audio_retention: bool = False
    background_capture: bool = False


async def transcribe_foreground_audio(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    device_id: uuid.UUID,
    transmit_grant_id: uuid.UUID,
    language: SupportedLanguage,
    consent: ForegroundConsent,
    ephemeral_audio: bytes,
    provider: AiProviderBoundary,
    now: datetime | None = None,
    request_id: uuid.UUID | None = None,
) -> TranscriptionReceipt:
    """Transcribe bounded in-memory audio only for an active caller-owned transmit grant."""
    resolved_now = now or datetime.now(UTC)

    if (
        consent.user_initiated is not True
        or consent.foreground_only is not True
        or consent.background_capture is not False
        or consent.durable_audio_retention is not False
    ):
        raise TranscriptionError(
            "AI_TRANSCRIPTION_CONSENT_REQUIRED",
            "Foreground transcription consent is required.",
        )

    grant = await db.scalar(
        select(MediaGrant).where(
            MediaGrant.id == transmit_grant_id,
            MediaGrant.account_id == account_id,
            MediaGrant.device_id == device_id,
            MediaGrant.grant_kind == "transmit",
            MediaGrant.revoked_at.is_(None),
            MediaGrant.expires_at > resolved_now,
            MediaGrant.action_scope == "microphone_publish",
        )
    )
    if grant is None:
        raise TranscriptionError(
            "AI_TRANSCRIPTION_NOT_AUTHORIZED",
            "An active caller-owned transmit grant is required.",
        )

    resolved_request_id = request_id or uuid.uuid4()
    try:
        result = await provider.transcribe(
            AiTranscriptionRequest(
                request_id=resolved_request_id,
                language=language,
                ephemeral_audio=ephemeral_audio,
            )
        )
    except AiProviderUnavailable as exc:
        raise TranscriptionError(
            "AI_TRANSCRIPTION_UNAVAILABLE",
            "Transcription is unavailable.",
        ) from exc

    return TranscriptionReceipt(
        request_id=result.request_id,
        transmit_grant_id=grant.id,
        transcript=result.output_text,
        language=language,
        provider_mode=result.provider_mode,
        completed_at=resolved_now,
    )
