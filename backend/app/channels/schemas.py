import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class PrivateChannelCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_label: str = Field(min_length=1, max_length=64)


class PrivateChannelJoinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invite: str = Field(min_length=40, max_length=128, repr=False)


class PrivateChannelResponse(ChannelSummaryResponse):
    created_at: datetime


class PrivateChannelInviteResponse(PrivateChannelResponse):
    invite: str | None = Field(default=None, min_length=40, max_length=128, repr=False)
    replayed: bool


class ChannelLifecycleResponse(BaseModel):
    channel_id: uuid.UUID
    state: Literal["joined", "left", "closed"]
    changed_at: datetime
    replayed: bool
