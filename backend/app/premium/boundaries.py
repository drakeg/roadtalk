from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PremiumResponsibility(StrEnum):
    CANCELLATION = "cancellation"
    REFUND = "refund"
    CHARGEBACK = "chargeback"
    TAX = "tax"
    APP_STORE_POLICY = "app_store_policy"
    MERCHANT_OF_RECORD = "merchant_of_record"


class PremiumBoundaryDisposition(StrEnum):
    DETERMINISTIC_ONLY = "deterministic_only"
    LIVE_APPROVAL_REQUIRED = "live_approval_required"


class PremiumBoundaryDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    responsibility: PremiumResponsibility
    disposition: PremiumBoundaryDisposition
    implemented_live: Literal[False] = False
    recurring_cost_usd: Literal[0] = 0
    requires_separate_approval: Literal[True] = True


def premium_live_responsibility_boundary(
    responsibility: PremiumResponsibility,
) -> PremiumBoundaryDecision:
    return PremiumBoundaryDecision(
        responsibility=responsibility,
        disposition=PremiumBoundaryDisposition.LIVE_APPROVAL_REQUIRED,
    )


class PremiumCompatibilityBaseline(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    python_major_minor: Literal["3.14"] = "3.14"
    node_major: Literal[26] = 26
    react_native_major_minor: Literal["0.86"] = "0.86"
    expo_sdk_major: Literal[57] = 57
    premium_provider_modes: tuple[Literal["disabled", "test"], ...] = ("disabled", "test")
    live_payment_provider_enabled: Literal[False] = False
    recurring_cost_usd: Literal[0] = 0


SUPPORTED_PREMIUM_COMPATIBILITY = PremiumCompatibilityBaseline()
