import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChannelSummaryResponse(BaseModel):
    id: uuid.UUID
    slug: str | None
    display_label: str
    type: Literal["public", "private"]
    selected: bool
    enabled: bool
    version: int = Field(ge=1)


class ChannelCatalogResponse(BaseModel):
    items: tuple[ChannelSummaryResponse, ...]


class ChannelSelectionResponse(ChannelSummaryResponse):
    selected: Literal[True] = True
    selected_at: datetime
    selection_version: int = Field(ge=1)
