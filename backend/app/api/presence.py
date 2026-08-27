from fastapi import APIRouter, Request

from app.api.auth import CurrentSession, DatabaseSession
from app.presence.lifecycle import PRESENCE_POLICY_VERSION, current_presence_snapshot
from app.presence.policy import PRESENCE_CELL_SIZE_M, PRESENCE_MIN_VISIBLE_ACCOUNTS
from app.presence.schemas import NearbyPresenceQuery, NearbyPresenceResponse, PresenceCellResponse

router = APIRouter(prefix="/api/v1/presence", tags=["presence"])


@router.get("/nearby", response_model=NearbyPresenceResponse)
async def read_nearby_presence(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
    query: NearbyPresenceQuery,
) -> NearbyPresenceResponse:
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
