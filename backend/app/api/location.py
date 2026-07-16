import time
from typing import Literal, cast

from fastapi import APIRouter, HTTPException, Request, status

from app.api.auth import CurrentSession, DatabaseSession
from app.location.consent import LocationConsentError, set_foreground_location_consent
from app.location.limiter import LocationLimiter, LocationRateLimitError
from app.location.nearby import NearbySummaryError, get_nearby_summary
from app.location.quality import LocationPolicyError, LocationSample, policy_from_settings
from app.location.schemas import (
    CurrentLocationPauseResponse,
    CurrentLocationRequest,
    CurrentLocationResponse,
    LocationConsentRequest,
    LocationConsentResponse,
    NearbySummaryResponse,
)
from app.location.service import delete_current_location, record_current_location

router = APIRouter(prefix="/api/v1/me", tags=["location"])
nearby_router = APIRouter(prefix="/api/v1/nearby", tags=["location"])


def _check_mutation_limit(
    request: Request,
    current: CurrentSession,
) -> None:
    limiter = cast(LocationLimiter, request.app.state.location_limiter)
    peer = request.client.host if request.client is not None else "unknown"
    try:
        limiter.check_mutation(
            peer=peer,
            account_id=str(current.account.id),
            device_id=str(current.device.id),
            now=time.monotonic(),
        )
    except LocationRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "LOCATION_RATE_LIMITED",
                "detail": "Location requests are temporarily limited.",
            },
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


def _policy_error(exc: LocationPolicyError) -> HTTPException:
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    if exc.code in {
        "LOCATION_CONSENT_REQUIRED",
        "LOCATION_POLICY_MISMATCH",
        "LOCATION_SAMPLE_CONFLICT",
        "LOCATION_SAMPLE_OUT_OF_ORDER",
    }:
        status_code = status.HTTP_409_CONFLICT
    elif exc.code == "LOCATION_SOURCE_INVALID":
        status_code = status.HTTP_403_FORBIDDEN
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "detail": exc.detail},
    )


def _check_nearby_limit(request: Request, current: CurrentSession) -> None:
    limiter = cast(LocationLimiter, request.app.state.location_limiter)
    peer = request.client.host if request.client is not None else "unknown"
    try:
        limiter.check_nearby_read(
            peer=peer,
            account_id=str(current.account.id),
            device_id=str(current.device.id),
            now=time.monotonic(),
        )
    except LocationRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "LOCATION_RATE_LIMITED",
                "detail": "Location requests are temporarily limited.",
            },
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


async def _set_consent_decision(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
    decision: Literal["granted", "revoked"],
    payload: LocationConsentRequest | None = None,
) -> LocationConsentResponse:
    _check_mutation_limit(request, current)
    settings = request.app.state.settings
    try:
        receipt = await set_foreground_location_consent(
            db,
            account_id=current.account.id,
            device_id=current.device.id,
            platform=current.device.platform,
            decision=decision,
            requested_policy_version=payload.policy_version if payload is not None else None,
            requested_disclosure_version=(
                payload.disclosure_version if payload is not None else None
            ),
            current_policy_version=settings.location_policy_version,
            current_disclosure_version=settings.location_disclosure_version,
        )
    except LocationConsentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": exc.code, "detail": exc.detail},
        ) from exc
    return LocationConsentResponse(**receipt.__dict__)


@router.put("/location-consent", response_model=LocationConsentResponse)
async def grant_location_consent(
    request: Request,
    payload: LocationConsentRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> LocationConsentResponse:
    return await _set_consent_decision(request, db, current, "granted", payload)


@router.delete("/location-consent", response_model=LocationConsentResponse)
async def revoke_location_consent(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
) -> LocationConsentResponse:
    return await _set_consent_decision(request, db, current, "revoked")


@router.put("/location", response_model=CurrentLocationResponse)
async def put_current_location(
    request: Request,
    payload: CurrentLocationRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> CurrentLocationResponse:
    _check_mutation_limit(request, current)
    try:
        receipt = await record_current_location(
            db,
            account_id=current.account.id,
            device_id=current.device.id,
            sample=LocationSample(**payload.model_dump()),
            policy=policy_from_settings(request.app.state.settings),
        )
    except LocationPolicyError as exc:
        raise _policy_error(exc) from exc
    return CurrentLocationResponse(**receipt.__dict__)


@router.delete("/location", response_model=CurrentLocationPauseResponse)
async def pause_current_location(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
) -> CurrentLocationPauseResponse:
    _check_mutation_limit(request, current)
    await delete_current_location(db, account_id=current.account.id)
    return CurrentLocationPauseResponse()


@nearby_router.get("/summary", response_model=NearbySummaryResponse)
async def read_nearby_summary(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
) -> NearbySummaryResponse:
    _check_nearby_limit(request, current)
    settings = request.app.state.settings
    try:
        summary = await get_nearby_summary(
            db,
            account_id=current.account.id,
            policy_version=settings.location_policy_version,
            max_usable_accuracy_m=settings.location_max_usable_accuracy_m,
            radius_m=settings.location_nearby_radius_m,
            many_threshold=settings.location_nearby_many_threshold,
        )
    except NearbySummaryError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": exc.code, "detail": exc.detail},
        ) from exc
    return NearbySummaryResponse(**summary.__dict__)
