from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NearbyPresenceQuery(BaseModel):
    """Intentionally empty: clients cannot select people, cells, radius, or providers."""

    model_config = ConfigDict(extra="forbid")


class PresenceCellResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    approximate_latitude: float = Field(ge=-85.051129, le=85.051129)
    approximate_longitude: float = Field(ge=-180, le=180)
    cell_size_m: Literal[2000] = 2000
    density: Literal["few", "several", "many"]


class NearbyPresenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    availability: Literal["available"] = "available"
    policy_version: Literal["presence-v1"] = "presence-v1"
    privacy_min_accounts: Literal[3] = 3
    freshness: Literal["fresh"] = "fresh"
    expires_at: datetime
    cells: tuple[PresenceCellResponse, ...]
