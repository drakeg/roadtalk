import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ConvoyState = Literal["active", "disbanded"]
ConvoyMembershipRole = Literal["leader", "member"]
ConvoyMembershipState = Literal["active", "left", "revoked", "expired"]


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConvoyPublicSummary(ClosedModel):
    convoy_id: uuid.UUID
    display_name: str = Field(min_length=1, max_length=64)
    state: ConvoyState


class ConvoyMemberSummary(ClosedModel):
    account_id: uuid.UUID
    callsign: str = Field(min_length=1, max_length=64)
    role: ConvoyMembershipRole
    state: Literal["active"] = "active"


class ConvoyMembershipContext(ClosedModel):
    convoy_id: uuid.UUID
    membership_id: uuid.UUID
    role: ConvoyMembershipRole
    state: ConvoyMembershipState
    expires_at: datetime | None = None
    context_only: Literal[True] = True
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )


class ConvoyAwarenessMember(ClosedModel):
    account_id: uuid.UUID
    callsign: str = Field(min_length=1, max_length=64)
    role: ConvoyMembershipRole
    availability: Literal["current"] = "current"
    expires_at: datetime


class ConvoyAwarenessSnapshot(ClosedModel):
    convoy_id: uuid.UUID
    freshness: Literal["current"] = "current"
    expires_at: datetime
    members: tuple[ConvoyAwarenessMember, ...]


class ConvoyJoinRequest(ClosedModel):
    invite: str = Field(min_length=40, max_length=128, repr=False)


class ConvoyLifecycleResponse(ClosedModel):
    convoy_id: uuid.UUID
    membership_id: uuid.UUID | None = None
    state: Literal["joined", "left", "revoked", "expired", "disbanded"]
    changed_at: datetime


PROHIBITED_CONVOY_FIELDS = frozenset(
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
        "background_location",
        "background_audio",
        "microphone",
        "username",
        "email",
        "phone",
        "password",
        "password_hash",
        "recovery_key",
        "access_token",
        "refresh_token",
        "provider",
        "provider_key",
        "provider_token",
        "api_key",
        "recipient_id",
        "recipient_ids",
        "audience_override",
        "nearby_users",
        "non_members",
        "all_users",
    }
)
