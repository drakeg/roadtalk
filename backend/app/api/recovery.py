import hashlib
import time
import uuid
from typing import cast

from fastapi import APIRouter, HTTPException, Request, status

from app.api.auth import CurrentSession, DatabaseSession
from app.ptt.provider import MediaProvider
from app.ptt.service import reconcile_media_grants, reconcile_proximity_delivery
from app.recovery.limiter import RecoveryLimiter, RecoveryRateLimitError
from app.recovery.schemas import (
    RecoveryKeyResponse,
    RecoverySessionRequest,
    RecoverySessionResponse,
)
from app.recovery.security import recovery_key_id
from app.recovery.service import (
    RecoveryError,
    create_or_rotate_recovery_key,
    recover_account,
)

router = APIRouter(tags=["recovery"])


async def _reconcile_recovery_change(
    request: Request,
    db: DatabaseSession,
    account_id: uuid.UUID,
) -> None:
    del account_id
    await reconcile_proximity_delivery(
        db,
        provider=cast(MediaProvider, request.app.state.media_provider),
        settings=request.app.state.settings,
    )
    await reconcile_media_grants(
        db,
        provider=cast(MediaProvider, request.app.state.media_provider),
    )


def rate_limit_error(exc: RecoveryRateLimitError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "code": "RECOVERY_RATE_LIMITED",
            "detail": "Recovery requests are temporarily limited.",
        },
        headers={"Retry-After": str(exc.retry_after)},
    )


@router.post(
    "/api/v1/me/recovery-key",
    response_model=RecoveryKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def rotate_recovery_key(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
) -> RecoveryKeyResponse:
    limiter = cast(RecoveryLimiter, request.app.state.recovery_limiter)
    try:
        limiter.check_mutation(
            account_id=str(current.account.id),
            device_id=str(current.device.id),
            now=time.monotonic(),
        )
    except RecoveryRateLimitError as exc:
        raise rate_limit_error(exc) from exc
    try:
        return await create_or_rotate_recovery_key(
            db,
            account_id=current.account.id,
            settings=request.app.state.settings,
        )
    except RecoveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": exc.code, "detail": exc.detail},
        ) from exc


@router.post(
    "/api/v1/sessions/recover",
    response_model=RecoverySessionResponse,
)
async def recover_session(
    request: Request,
    payload: RecoverySessionRequest,
    db: DatabaseSession,
) -> RecoverySessionResponse:
    raw_key = payload.recovery_key.get_secret_value()
    parsed_key_id = recovery_key_id(raw_key)
    selector = hashlib.sha256(
        (str(parsed_key_id) if parsed_key_id is not None else "invalid").encode("ascii")
    ).hexdigest()
    peer = request.client.host if request.client is not None else "unknown"
    limiter = cast(RecoveryLimiter, request.app.state.recovery_limiter)
    try:
        limiter.check_attempt(
            peer=peer,
            installation_id=payload.installation_id,
            selector=selector,
            now=time.monotonic(),
        )
    except RecoveryRateLimitError as exc:
        raise rate_limit_error(exc) from exc

    try:
        return await recover_account(
            db,
            raw_key=raw_key,
            installation_id=payload.installation_id,
            platform=payload.platform,
            settings=request.app.state.settings,
            on_change=lambda session, account_id: _reconcile_recovery_change(
                request, session, account_id
            ),
        )
    except RecoveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "RECOVERY_FAILED", "detail": str(exc)},
        ) from exc
