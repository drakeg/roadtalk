from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from app.api.auth import CurrentSession, DatabaseSession
from app.campgrounds.catalog import DETERMINISTIC_CAMPGROUNDS
from app.campgrounds.context import derive_current_campground_context
from app.campgrounds.contracts import CampgroundContextLabel, CampgroundPublicRecord

router = APIRouter(prefix="/api/v1/campgrounds", tags=["campgrounds"])


class CampgroundCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = "deterministic_local"
    freshness: str = "deterministic"
    live_directory: bool = False
    campgrounds: tuple[CampgroundPublicRecord, ...]


class CurrentCampgroundResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: str
    context: CampgroundContextLabel | None = None
    expires_at: datetime | None = None


@router.get("/catalog", response_model=CampgroundCatalogResponse)
async def read_campground_catalog() -> CampgroundCatalogResponse:
    """Return only the deterministic, bounded Sprint 10 catalog."""

    return CampgroundCatalogResponse(campgrounds=DETERMINISTIC_CAMPGROUNDS)


@router.get("/context", response_model=CurrentCampgroundResponse)
async def read_current_campground_context(
    request: Request,
    db: DatabaseSession,
    current: CurrentSession,
) -> CurrentCampgroundResponse:
    """Return ephemeral server-derived context; client selectors are forbidden."""

    if request.query_params:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "CAMPGROUND_CONTEXT_SELECTOR_FORBIDDEN",
                "detail": "Current campground context does not accept selectors.",
            },
        )
    context = await derive_current_campground_context(
        db,
        account_id=current.account.id,
        location_policy_version=request.app.state.settings.location_policy_version,
    )
    if context is None:
        return CurrentCampgroundResponse(state="unavailable")
    return CurrentCampgroundResponse(
        state="current",
        context=context.label,
        expires_at=context.expires_at,
    )
