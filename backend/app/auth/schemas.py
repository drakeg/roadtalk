import uuid
from typing import Literal

from pydantic import BaseModel, Field


class AnonymousSessionRequest(BaseModel):
    installation_id: str = Field(min_length=16, max_length=255)
    platform: Literal["android", "ios"]


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class AnonymousSessionResponse(TokenPair):
    account_id: uuid.UUID
    device_id: uuid.UUID
    session_id: uuid.UUID


class SessionIdentity(BaseModel):
    account_id: uuid.UUID
    device_id: uuid.UUID
    session_id: uuid.UUID
    account_type: str


class LogoutResponse(BaseModel):
    status: Literal["logged_out"] = "logged_out"


class DeviceRevocationResponse(BaseModel):
    device_id: uuid.UUID
    revoked_sessions: int
