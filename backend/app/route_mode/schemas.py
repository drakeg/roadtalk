from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RouteMode = Literal["nearby", "same_road"]
RouteModeAvailability = Literal["available", "unavailable"]


class RouteModeResponse(BaseModel):
    mode: RouteMode
    version: int = Field(ge=1)
    selected_at: datetime
    availability: RouteModeAvailability


class RouteModeUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: RouteMode
    expected_version: int = Field(ge=1)
