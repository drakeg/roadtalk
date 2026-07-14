import time
from typing import Annotated, cast

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.auth import CurrentSession, DatabaseSession
from app.identity.callsigns import CallsignAvailabilityLimiter, CallsignRateLimitError
from app.identity.schemas import CallsignAvailabilityResponse
from app.identity.service import callsign_availability

router = APIRouter(prefix="/api/v1/callsigns", tags=["identity"])


@router.get("/availability", response_model=CallsignAvailabilityResponse)
async def availability(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
    candidate: Annotated[str, Query(alias="callsign", min_length=1, max_length=128)],
) -> CallsignAvailabilityResponse:
    limiter = cast(CallsignAvailabilityLimiter, request.app.state.callsign_limiter)
    try:
        limiter.check(
            account_id=current.account.id,
            device_id=current.device.id,
            now=time.monotonic(),
        )
    except CallsignRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "CALLSIGN_RATE_LIMITED",
                "detail": "Callsign availability checks are temporarily limited.",
            },
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc

    return await callsign_availability(
        db,
        account_id=current.account.id,
        candidate=candidate,
    )
