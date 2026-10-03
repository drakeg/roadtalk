from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ai.contracts import AuthorizedTextSourceKind, SupportedLanguage
from app.ai.provider import AiProviderBoundary, AiProviderUnavailable, AiTextRequest

SUMMARY_SOURCE_MAX_CHARS = 8_000
SUMMARY_RESULT_MAX_CHARS = 4_000


class SummaryError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class AuthorizedSummarySource(BaseModel):
    """Server-internal already-authorized text snapshot; never an external authorization input."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: uuid.UUID
    source_kind: AuthorizedTextSourceKind
    text: str = Field(min_length=1, max_length=SUMMARY_SOURCE_MAX_CHARS)
    language: SupportedLanguage
    authorized_only: Literal[True] = True
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )
    observed_at: datetime
    expires_at: datetime

    @field_validator("observed_at", "expires_at")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("summary source timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def expiry_must_follow_observation(self) -> AuthorizedSummarySource:
        if self.expires_at <= self.observed_at:
            raise ValueError("summary source expiry must follow observation")
        return self


@dataclass(frozen=True, slots=True)
class SummaryReceipt:
    request_id: uuid.UUID
    source_id: uuid.UUID
    source_kind: AuthorizedTextSourceKind
    summary: str
    source_language: SupportedLanguage
    state: Literal["ready"]
    provider_mode: Literal["test"]
    generated_at: datetime
    source_expires_at: datetime
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )


async def summarize_authorized_text(
    *,
    source: AuthorizedSummarySource,
    provider: AiProviderBoundary,
    max_output_chars: int = 1_200,
    now: datetime | None = None,
    request_id: uuid.UUID | None = None,
) -> SummaryReceipt:
    """Summarize already-authorized bounded text without creating new eligibility."""
    resolved_now = now or datetime.now(UTC)

    if not 1 <= max_output_chars <= SUMMARY_RESULT_MAX_CHARS:
        raise SummaryError("AI_SUMMARY_BOUNDS_INVALID", "Summary output bounds are invalid.")
    if source.expires_at <= resolved_now:
        raise SummaryError("AI_SUMMARY_SOURCE_STALE", "The summary source is no longer current.")
    if source.authorized_only is not True or (
        source.authorization_source != "existing_roadtalk_authorization"
    ):
        raise SummaryError("AI_SUMMARY_NOT_AUTHORIZED", "The summary source is not authorized.")

    resolved_request_id = request_id or uuid.uuid4()
    try:
        result = await provider.process_text(
            AiTextRequest(
                request_id=resolved_request_id,
                capability="summary",
                input_text=source.text,
                source_language=source.language,
            )
        )
    except AiProviderUnavailable as exc:
        raise SummaryError("AI_SUMMARY_UNAVAILABLE", "Summary is unavailable.") from exc

    if len(result.output_text) > max_output_chars:
        raise SummaryError("AI_SUMMARY_OUTPUT_INVALID", "Summary output exceeded its safe bound.")

    return SummaryReceipt(
        request_id=result.request_id,
        source_id=source.source_id,
        source_kind=source.source_kind,
        summary=result.output_text,
        source_language=source.language,
        state="ready",
        provider_mode=result.provider_mode,
        generated_at=resolved_now,
        source_expires_at=source.expires_at,
    )
