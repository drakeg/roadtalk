import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AiCapability = Literal["transcription", "summary", "translation"]
AiState = Literal["requested", "ready", "unavailable", "expired"]
AuthorizedTextSourceKind = Literal["transcript", "message_window"]
SupportedLanguage = Literal["en", "es", "fr", "de"]


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ForegroundConsent(ClosedModel):
    user_initiated: Literal[True] = True
    foreground_only: Literal[True] = True
    background_capture: Literal[False] = False
    durable_audio_retention: Literal[False] = False


class AuthorizedTextSource(ClosedModel):
    source_id: uuid.UUID
    source_kind: AuthorizedTextSourceKind
    authorized_only: Literal[True] = True
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )


class TranscriptionIntent(ClosedModel):
    session_id: uuid.UUID
    language: SupportedLanguage
    consent: ForegroundConsent
    capability: Literal["transcription"] = "transcription"


class SummaryCommand(ClosedModel):
    source: AuthorizedTextSource
    max_output_chars: int = Field(default=1200, ge=1, le=4000)
    capability: Literal["summary"] = "summary"


class TranslationCommand(ClosedModel):
    source: AuthorizedTextSource
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    max_output_chars: int = Field(default=4000, ge=1, le=8000)
    capability: Literal["translation"] = "translation"

    @model_validator(mode="after")
    def target_must_differ(self) -> "TranslationCommand":
        if self.source_language == self.target_language:
            raise ValueError("target language must differ from source language")
        return self


class AiResultContext(ClosedModel):
    capability: AiCapability
    state: AiState
    source_id: uuid.UUID
    source_kind: AuthorizedTextSourceKind
    source_language: SupportedLanguage | None = None
    target_language: SupportedLanguage | None = None
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )
    provider_mode: Literal["disabled", "test"] = "disabled"
    durable_audio_retention: Literal[False] = False
    background_capture: Literal[False] = False


PROHIBITED_AI_FIELDS = frozenset(
    {
        "latitude",
        "longitude",
        "coordinates",
        "position",
        "location",
        "location_history",
        "route",
        "route_history",
        "corridor",
        "destination",
        "heading",
        "speed",
        "audio",
        "audio_bytes",
        "audio_url",
        "audio_recording",
        "recording",
        "recording_url",
        "background_audio",
        "background_location",
        "microphone_stream",
        "attachment",
        "evidence",
        "password",
        "password_hash",
        "recovery_key",
        "access_token",
        "refresh_token",
        "provider",
        "provider_key",
        "provider_token",
        "api_key",
        "model",
        "model_id",
        "prompt",
        "system_prompt",
        "recipient_ids",
        "audience_override",
        "nearby_users",
        "all_users",
        "authorization_override",
        "enforcement_override",
        "tracking_id",
        "analytics_profile",
        "marketing_profile",
    }
)
