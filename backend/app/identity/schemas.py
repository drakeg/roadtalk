from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CallsignAvailabilityResponse(BaseModel):
    available: bool
    reason: Literal["available", "invalid", "reserved", "taken"]


class PublicIdentity(BaseModel):
    callsign: str | None
    avatar_id: str | None


class ProfileResponse(BaseModel):
    identity: PublicIdentity
    setup_completed: bool
    version: int = Field(ge=0)


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=0)
    callsign: str = Field(min_length=1, max_length=128)
