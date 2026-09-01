from datetime import datetime, timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NotificationClass = Literal["account", "channel_activity", "urgent_alert"]
NotificationPriority = Literal["normal", "high", "urgent"]
NotificationSource = Literal["roadtalk_account", "roadtalk_channel", "user_generated_urgent"]

ACCOUNT_MAX_TTL = timedelta(days=7)
CHANNEL_ACTIVITY_MAX_TTL = timedelta(hours=2)
URGENT_ALERT_MAX_TTL = timedelta(minutes=10)
URGENT_ALERT_MAX_MESSAGE_LENGTH = 280

URGENT_ALERT_NOT_EMERGENCY_SERVICE: Literal["RoadTalk is not an emergency service."] = (
    "RoadTalk is not an emergency service."
)
URGENT_ALERT_DELIVERY_NOT_GUARANTEED: Literal["Delivery is not guaranteed."] = (
    "Delivery is not guaranteed."
)
URGENT_ALERT_EMERGENCY_SERVICES_GUIDANCE: Literal[
    "Contact local emergency services directly when emergency assistance is needed."
] = "Contact local emergency services directly when emergency assistance is needed."
URGENT_ALERT_UNVERIFIED: Literal["This alert is user-generated and unverified."] = (
    "This alert is user-generated and unverified."
)


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AccountNotificationPayload(ClosedModel):
    notification_class: Literal["account"] = "account"
    priority: Literal["normal", "high"]
    source: Literal["roadtalk_account"] = "roadtalk_account"
    title: Annotated[str, Field(min_length=1, max_length=96)]
    message: Annotated[str, Field(min_length=1, max_length=280)]
    issued_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_expiry(self) -> "AccountNotificationPayload":
        _validate_expiry(self.issued_at, self.expires_at, ACCOUNT_MAX_TTL)
        return self


class ChannelActivityNotificationPayload(ClosedModel):
    notification_class: Literal["channel_activity"] = "channel_activity"
    priority: Literal["normal", "high"]
    source: Literal["roadtalk_channel"] = "roadtalk_channel"
    title: Annotated[str, Field(min_length=1, max_length=96)]
    message: Annotated[str, Field(min_length=1, max_length=280)]
    channel_label: Annotated[str, Field(min_length=1, max_length=64)]
    issued_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_expiry(self) -> "ChannelActivityNotificationPayload":
        _validate_expiry(self.issued_at, self.expires_at, CHANNEL_ACTIVITY_MAX_TTL)
        return self


class UrgentAlertNotificationPayload(ClosedModel):
    notification_class: Literal["urgent_alert"] = "urgent_alert"
    priority: Literal["urgent"] = "urgent"
    source: Literal["user_generated_urgent"] = "user_generated_urgent"
    message: Annotated[str, Field(min_length=1, max_length=URGENT_ALERT_MAX_MESSAGE_LENGTH)]
    issued_at: datetime
    expires_at: datetime
    verified: Literal[False] = False
    emergency_service: Literal[False] = False
    delivery_guaranteed: Literal[False] = False
    safety_not_emergency_service: Literal["RoadTalk is not an emergency service."] = (
        URGENT_ALERT_NOT_EMERGENCY_SERVICE
    )
    safety_delivery_not_guaranteed: Literal["Delivery is not guaranteed."] = (
        URGENT_ALERT_DELIVERY_NOT_GUARANTEED
    )
    safety_emergency_services_guidance: Literal[
        "Contact local emergency services directly when emergency assistance is needed."
    ] = URGENT_ALERT_EMERGENCY_SERVICES_GUIDANCE
    safety_unverified: Literal["This alert is user-generated and unverified."] = (
        URGENT_ALERT_UNVERIFIED
    )

    @model_validator(mode="after")
    def validate_expiry(self) -> "UrgentAlertNotificationPayload":
        _validate_expiry(self.issued_at, self.expires_at, URGENT_ALERT_MAX_TTL)
        return self


NotificationPayload = Annotated[
    AccountNotificationPayload
    | ChannelActivityNotificationPayload
    | UrgentAlertNotificationPayload,
    Field(discriminator="notification_class"),
]


class UrgentAlertCommand(ClosedModel):
    message: Annotated[str, Field(min_length=1, max_length=URGENT_ALERT_MAX_MESSAGE_LENGTH)]
    idempotency_key: Annotated[str, Field(min_length=16, max_length=128)]


PROHIBITED_NOTIFICATION_FIELDS = frozenset(
    {
        "recipient_id",
        "recipient_ids",
        "account_id",
        "device_id",
        "installation_id",
        "username",
        "password",
        "recovery_key",
        "refresh_token",
        "access_token",
        "push_token",
        "provider",
        "provider_ref",
        "provider_token",
        "latitude",
        "longitude",
        "coordinates",
        "radius",
        "radius_m",
        "distance",
        "distance_m",
        "bearing",
        "heading",
        "speed",
        "route",
        "corridor",
        "destination",
        "history",
    }
)


def _validate_expiry(issued_at: datetime, expires_at: datetime, maximum: timedelta) -> None:
    if expires_at <= issued_at:
        raise ValueError("expires_at must be after issued_at")
    if expires_at - issued_at > maximum:
        raise ValueError("notification expiry exceeds the allowed lifetime")
