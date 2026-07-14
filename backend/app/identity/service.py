import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.identity.callsigns import CallsignPolicyError, validate_callsign
from app.identity.schemas import CallsignAvailabilityResponse


async def callsign_availability(
    db: AsyncSession,
    *,
    account_id: uuid.UUID,
    candidate: str,
) -> CallsignAvailabilityResponse:
    try:
        callsign = validate_callsign(candidate)
    except CallsignPolicyError as exc:
        reason = "reserved" if exc.code == "CALLSIGN_RESERVED" else "invalid"
        return CallsignAvailabilityResponse(available=False, reason=reason)

    owner = await db.scalar(
        select(Profile.account_id).where(
            Profile.normalized_callsign == callsign.normalized,
            Profile.account_id != account_id,
        )
    )
    if owner is not None:
        return CallsignAvailabilityResponse(available=False, reason="taken")
    return CallsignAvailabilityResponse(available=True, reason="available")
