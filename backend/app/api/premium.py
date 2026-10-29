from datetime import UTC, datetime

from fastapi import APIRouter, Request, Response

from app.api.auth import CurrentSession
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
    # Entitlement is per-account and short-lived; intermediaries must not reuse it.
    response.headers["Cache-Control"] = "no-store"
    return await read_premium_status(
        boundary,
        account_id=current.account.id,
        now=datetime.now(UTC),
    )
