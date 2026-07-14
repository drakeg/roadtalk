from typing import Literal

from pydantic import BaseModel, Field, SecretStr

from app.auth.schemas import AnonymousSessionResponse


class RecoveryKeyResponse(BaseModel):
    recovery_key: str
    key_version: Literal["rtk1"] = "rtk1"


class RecoverySessionRequest(BaseModel):
    recovery_key: SecretStr
    installation_id: str = Field(min_length=16, max_length=255)
    platform: Literal["android", "ios"]


class RecoverySessionResponse(AnonymousSessionResponse):
    recovery_key: str
    recovery_key_version: Literal["rtk1"] = "rtk1"
