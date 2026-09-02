import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferencesResponse(BaseModel):
    channel_activity_enabled: bool
    urgent_alert_enabled: bool
    version: int = Field(ge=1)


class NotificationPreferencesUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_activity_enabled: bool
    urgent_alert_enabled: bool
    expected_version: int = Field(ge=1)


class NotificationRecordResponse(BaseModel):
    id: uuid.UUID
    notification_class: Literal["account", "channel_activity", "urgent_alert"]
    priority: Literal["normal", "high", "urgent"]
    source: Literal["roadtalk_account", "roadtalk_channel", "user_generated_urgent"]
    title: str | None
    message: str
    channel_label: str | None
    issued_at: datetime
    expires_at: datetime
    read_at: datetime | None
    dismissed_at: datetime | None
    version: int = Field(ge=1)
    verified: Literal[False] | None
    emergency_service: Literal[False] | None
    delivery_guaranteed: Literal[False] | None
    safety_not_emergency_service: Literal["RoadTalk is not an emergency service."] | None
    safety_delivery_not_guaranteed: Literal["Delivery is not guaranteed."] | None
    safety_emergency_services_guidance: (
        Literal["Contact local emergency services directly when emergency assistance is needed."]
        | None
    )
    safety_unverified: Literal["This alert is user-generated and unverified."] | None


class NotificationInboxResponse(BaseModel):
    items: tuple[NotificationRecordResponse, ...]


class NotificationStateUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["read", "dismissed"]
    expected_version: int = Field(ge=1)


class UrgentAlertCommandResponse(BaseModel):
    accepted: Literal[True] = True
    recipient_count: int = Field(ge=0)
    issued_at: datetime
    expires_at: datetime
