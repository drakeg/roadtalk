from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LocationConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(min_length=1, max_length=32)
    disclosure_version: str = Field(min_length=1, max_length=32)


class LocationConsentResponse(BaseModel):
    decision: Literal["granted", "revoked"]
    policy_version: str
    disclosure_version: str
    decided_at: datetime


class CurrentLocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    observed_at: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    horizontal_accuracy_m: float = Field(ge=0)
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    speed_mps: float | None = Field(default=None, ge=0)
    client_sequence: int = Field(ge=1)
    consent_policy_version: str = Field(min_length=1, max_length=32)


class CurrentLocationResponse(BaseModel):
    accepted_sequence: int = Field(ge=1)
    quality_state: Literal["usable", "degraded"]
    expires_at: datetime
    policy_version: str
    version: int = Field(ge=1)


class CurrentLocationPauseResponse(BaseModel):
    state: Literal["paused"] = "paused"
