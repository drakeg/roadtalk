import time
import uuid
from typing import Annotated, cast

from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from app.api.auth import CurrentSession, DatabaseSession
from app.ptt.limiter import PttLimiter, PttRateLimitError
from app.ptt.provider import MediaProvider
from app.ptt.schemas import GrantReleaseResponse, ReceiveGrantRequest, ReceiveGrantResponse
from app.ptt.service import GrantError, create_receive_grant, release_receive_grant

router = APIRouter(prefix="/api/v1/ptt/grants", tags=["push-to-talk"])
IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=16,
        max_length=128,
        pattern=r"^[A-Za-z0-9._~-]+$",
    ),
]


def _check_receive_limit(request: Request, current: CurrentSession) -> None:
    limiter = cast(PttLimiter, request.app.state.ptt_limiter)
    peer = request.client.host if request.client is not None else "unknown"
    try:
        limiter.check_receive(
            peer=peer,
            account_id=str(current.account.id),
            device_id=str(current.device.id),
            now=time.monotonic(),
        )
    except PttRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "PTT_RATE_LIMITED",
                "detail": "PTT grant requests are temporarily limited.",
            },
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


def _grant_error(exc: GrantError) -> HTTPException:
    status_code = status.HTTP_409_CONFLICT
    if exc.code == "PTT_GRANT_NOT_FOUND":
        status_code = status.HTTP_404_NOT_FOUND
    elif exc.code == "PTT_PROVIDER_UNAVAILABLE":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "detail": exc.detail},
    )


@router.post(
    "",
    response_model=ReceiveGrantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_grant(
    request: Request,
    response: Response,
    payload: ReceiveGrantRequest,
    idempotency_key: IdempotencyKey,
    db: DatabaseSession,
    current: CurrentSession,
) -> ReceiveGrantResponse:
    _check_receive_limit(request, current)
    try:
        receipt = await create_receive_grant(
            db,
            account_id=current.account.id,
            device_id=current.device.id,
            idempotency_key=idempotency_key,
            settings=request.app.state.settings,
            provider=cast(MediaProvider, request.app.state.media_provider),
        )
    except GrantError as exc:
        raise _grant_error(exc) from exc
    if receipt.replayed:
        response.status_code = status.HTTP_200_OK
    return ReceiveGrantResponse(**receipt.__dict__)


@router.delete("/{grant_id}", response_model=GrantReleaseResponse)
async def release_grant(
    grant_id: uuid.UUID,
    request: Request,
    idempotency_key: IdempotencyKey,
    db: DatabaseSession,
    current: CurrentSession,
) -> GrantReleaseResponse:
    del idempotency_key
    try:
        receipt = await release_receive_grant(
            db,
            account_id=current.account.id,
            device_id=current.device.id,
            grant_id=grant_id,
            provider=cast(MediaProvider, request.app.state.media_provider),
        )
    except GrantError as exc:
        raise _grant_error(exc) from exc
    return GrantReleaseResponse(**receipt.__dict__)
