from typing import Literal

from pydantic import BaseModel


class CallsignAvailabilityResponse(BaseModel):
    available: bool
    reason: Literal["available", "invalid", "reserved", "taken"]
