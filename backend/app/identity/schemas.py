from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CallsignAvailabilityResponse(BaseModel):
    available: bool
    reason: Literal["available", "invalid", "reserved", "taken"]


class AvatarCatalogItem(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=128)
    glyph: str = Field(min_length=1, max_length=4)
    background_color: str = Field(pattern=r"^#[0-9A-F]{6}$")
    foreground_color: str = Field(pattern=r"^#[0-9A-F]{6}$")
    status: Literal["active", "retired"]
    selectable: bool


class AvatarCatalogResponse(BaseModel):
    version: str = Field(min_length=1, max_length=32)
    avatars: list[AvatarCatalogItem]


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
    callsign: str | None = Field(default=None, min_length=1, max_length=128)
    avatar_id: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_mutation(self) -> Self:
        changed_fields = self.model_fields_set & {"callsign", "avatar_id"}
        if not changed_fields:
            raise ValueError("At least one profile field must be supplied.")
        if "callsign" in changed_fields and self.callsign is None:
            raise ValueError("Callsign cannot be null.")
        if "avatar_id" in changed_fields and self.avatar_id is None:
            raise ValueError("Avatar identifier cannot be null.")
        return self
