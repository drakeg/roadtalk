import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

PremiumTier = Literal["free", "premium"]
SubscriptionState = Literal[
    "inactive",
    "active",
    "grace",
    "canceled",
    "expired",
    "revoked",
]
EntitlementState = Literal["inactive", "active", "expired", "revoked"]
ProviderMode = Literal["disabled", "test"]


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PremiumAccountContext(ClosedModel):
    account_id: uuid.UUID
    tier: PremiumTier
    server_authoritative: Literal[True] = True
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )


class SubscriptionContext(ClosedModel):
    subscription_id: uuid.UUID
    account_id: uuid.UUID
    state: SubscriptionState
    provider_mode: ProviderMode = "disabled"
    observed_at: datetime
    expires_at: datetime | None = None
    server_authoritative: Literal[True] = True


class EntitlementContext(ClosedModel):
    entitlement_id: uuid.UUID
    account_id: uuid.UUID
    entitlement: Literal["premium"]
    state: EntitlementState
    observed_at: datetime
    expires_at: datetime | None = None
    server_authoritative: Literal[True] = True
    communication_authorization_unchanged: Literal[True] = True
    authorization_source: Literal["existing_roadtalk_authorization"] = (
        "existing_roadtalk_authorization"
    )


PROHIBITED_PREMIUM_FIELDS = frozenset(
    {
        "card_number",
        "card",
        "cvv",
        "cvc",
        "bank_account",
        "routing_number",
        "payment_method",
        "payment_method_token",
        "billing_address",
        "tax_id",
        "vat_id",
        "provider_secret",
        "provider_key",
        "provider_token",
        "api_key",
        "webhook_secret",
        "receipt",
        "purchase_token",
        "transaction_id",
        "latitude",
        "longitude",
        "coordinates",
        "location",
        "location_history",
        "route",
        "route_history",
        "heading",
        "speed",
        "nearby_users",
        "recipient_ids",
        "all_users",
        "password",
        "password_hash",
        "recovery_key",
        "access_token",
        "refresh_token",
        "analytics_profile",
        "marketing_profile",
        "authorization_override",
        "communication_override",
        "moderation_override",
    }
)
