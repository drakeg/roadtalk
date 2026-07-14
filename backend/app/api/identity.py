import time
from typing import Annotated, cast

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.auth import CurrentSession, DatabaseSession
from app.identity.callsigns import CallsignAvailabilityLimiter, CallsignRateLimitError
from app.identity.schemas import (
    CallsignAvailabilityResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.identity.service import (
    ProfileMutationError,
    callsign_availability,
    read_profile,
    update_profile,
)

router = APIRouter(tags=["identity"])


@router.get(
    "/api/v1/callsigns/availability",
    response_model=CallsignAvailabilityResponse,
)
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


@router.get("/api/v1/me/profile", response_model=ProfileResponse)
async def get_profile(db: DatabaseSession, current: CurrentSession) -> ProfileResponse:
    return await read_profile(db, account_id=current.account.id)


@router.patch("/api/v1/me/profile", response_model=ProfileResponse)
async def patch_profile(
    request: Request,
    payload: ProfileUpdateRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> ProfileResponse:
    try:
        return await update_profile(
            db,
            account_id=current.account.id,
            candidate=payload.callsign,
            expected_version=payload.version,
            cooldown_seconds=request.app.state.settings.callsign_change_cooldown_seconds,
        )
    except ProfileMutationError as exc:
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
        headers: dict[str, str] | None = None
        if exc.code in {"PROFILE_VERSION_CONFLICT", "CALLSIGN_UNAVAILABLE"}:
            status_code = status.HTTP_409_CONFLICT
        elif exc.code == "CALLSIGN_CHANGE_COOLDOWN":
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
            headers = {"Retry-After": str(exc.retry_after)}
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "detail": exc.detail},
            headers=headers,
        ) from exc
