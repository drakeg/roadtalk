from fastapi import APIRouter, HTTPException, Request, status

from app.api.auth import CurrentSession, DatabaseSession
from app.presence.lifecycle import PRESENCE_POLICY_VERSION, current_presence_snapshot
from app.presence.policy import PRESENCE_CELL_SIZE_M, PRESENCE_MIN_VISIBLE_ACCOUNTS
from app.presence.schemas import NearbyPresenceResponse, PresenceCellResponse

router = APIRouter(prefix="/api/v1/presence", tags=["presence"])


@router.get("/nearby", response_model=NearbyPresenceResponse)
async def read_nearby_presence(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
) -> NearbyPresenceResponse:
    if request.query_params:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "PRESENCE_SELECTOR_FORBIDDEN",
                "detail": "Presence does not accept selectors.",
            },
        )
    snapshot = await current_presence_snapshot(
        db,
        viewer_account_id=current.account.id,
        location_policy_version=request.app.state.settings.location_policy_version,
    )
    return NearbyPresenceResponse(
        policy_version=PRESENCE_POLICY_VERSION,
        privacy_min_accounts=PRESENCE_MIN_VISIBLE_ACCOUNTS,
        expires_at=snapshot.expires_at,
        cells=tuple(
            PresenceCellResponse(
                approximate_latitude=cell.approximate_latitude,
                approximate_longitude=cell.approximate_longitude,
                cell_size_m=PRESENCE_CELL_SIZE_M,
                density=cell.density,
            )
            for cell in snapshot.cells
        ),
    )
