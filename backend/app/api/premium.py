import time
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.auth import CurrentSession
from app.premium.limiter import PremiumRateLimitError, PremiumStatusLimiter
from app.premium.provider import PremiumProviderBoundary
from app.premium.status import PremiumStatus, read_premium_status

router = APIRouter(prefix="/api/v1/me", tags=["premium"])


@router.get("/premium", response_model=PremiumStatus)
async def read_my_premium_status(
    request: Request,
    response: Response,
    current: CurrentSession,
) -> PremiumStatus:
    boundary: PremiumProviderBoundary = request.app.state.premium_provider
    limiter: PremiumStatusLimiter = request.app.state.premium_status_limiter
    peer = request.client.host if request.client is not None else "unknown"
    try:
        limiter.check(
            peer=peer,
            account_id=str(current.account.id),
            device_id=str(current.device.id),
            now=time.monotonic(),
        )
    except PremiumRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Premium request is temporarily unavailable.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from None
    # Entitlement is per-account and short-lived; intermediaries must not reuse it.
    response.headers["Cache-Control"] = "no-store"
    return await read_premium_status(
        boundary,
        account_id=current.account.id,
        now=datetime.now(UTC),
    )
