import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ReportReason = Literal["harassment", "spam", "impersonation", "unsafe_content", "other"]
ReportState = Literal["submitted", "closed", "withdrawn"]
RestrictionKind = Literal["mute", "block"]
RestrictionState = Literal["active", "revoked", "expired"]


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReportCommand(ClosedModel):
    subject_account_id: uuid.UUID
    reason: ReportReason
    idempotency_key: str = Field(
        min_length=16, max_length=128, pattern=r"^[A-Za-z0-9._~-]+$"
    )


class ReportSummary(ClosedModel):
    report_id: uuid.UUID
    subject_account_id: uuid.UUID
    reason: ReportReason
    state: ReportState
    created_at: datetime


class RestrictionCommand(ClosedModel):
    subject_account_id: uuid.UUID
    kind: RestrictionKind


class RestrictionContext(ClosedModel):
    subject_account_id: uuid.UUID
    kind: RestrictionKind
    state: RestrictionState
    expires_at: datetime | None = None
    restrictive_only: Literal[True] = True
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )


PROHIBITED_MODERATION_FIELDS = frozenset(
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
        "audio_url",
        "audio_recording",
        "transcript",
        "attachment",
        "evidence",
        "free_text",
        "message",
        "notes",
        "background_location",
        "background_audio",
        "password",
        "password_hash",
        "recovery_key",
        "access_token",
        "refresh_token",
        "provider",
        "provider_key",
        "provider_token",
        "api_key",
        "recipient_ids",
        "audience_override",
        "nearby_users",
        "all_users",
        "moderator_notes",
        "enforcement_override",
        "authorization_override",
    }
)
