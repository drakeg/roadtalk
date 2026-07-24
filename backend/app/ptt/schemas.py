import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReceiveGrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["receive"] = "receive"


class ReceiveGrantResponse(BaseModel):
    grant_id: uuid.UUID
    mode: Literal["receive"] = "receive"
    provider: Literal["livekit"] = "livekit"
    room_ref: str
    participant_ref: str
    allowed_actions: tuple[Literal["join", "subscribe"], ...] = ("join", "subscribe")
    allowed_track_sources: tuple[str, ...] = ()
    issued_at: datetime
    expires_at: datetime
    policy_version: str
    replayed: bool
    server_url: str | None = None
    participant_token: str | None = Field(default=None, repr=False)


class GrantReleaseResponse(BaseModel):
    grant_id: uuid.UUID
    state: Literal["released"] = "released"
    released_at: datetime
    replayed: bool
