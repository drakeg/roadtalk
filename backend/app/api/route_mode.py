from typing import cast

from fastapi import APIRouter, HTTPException, Request, status

from app.api.auth import CurrentSession, DatabaseSession
from app.route_context.lifecycle import refresh_current_route_context
from app.route_context.provider import RouteContextProvider
from app.route_mode.schemas import RouteModeResponse, RouteModeUpdateRequest
from app.route_mode.service import RouteModeError, get_route_mode, set_route_mode

router = APIRouter(prefix="/api/v1", tags=["route-mode"])


def _route_mode_error(exc: RouteModeError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT
        if exc.code == "ROUTE_MODE_VERSION_CONFLICT"
        else status.HTTP_404_NOT_FOUND,
        detail={"code": exc.code, "detail": exc.detail},
    )


@router.get("/me/route-mode", response_model=RouteModeResponse)
async def read_route_mode(db: DatabaseSession, current: CurrentSession) -> RouteModeResponse:
    try:
        receipt = await get_route_mode(db, account_id=current.account.id)
    except RouteModeError as exc:
        raise _route_mode_error(exc) from exc
    return RouteModeResponse(**receipt.__dict__)


@router.put("/me/route-mode", response_model=RouteModeResponse)
async def update_route_mode(
    request: Request,
    payload: RouteModeUpdateRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> RouteModeResponse:
    try:
        receipt = await set_route_mode(
            db,
            account_id=current.account.id,
            mode=payload.mode,
            expected_version=payload.expected_version,
            on_change=lambda session, account_id: refresh_current_route_context(
                session,
                account_id=account_id,
                provider=cast(RouteContextProvider, request.app.state.route_context_provider),
                settings=request.app.state.settings,
            ),
        )
    except RouteModeError as exc:
        raise _route_mode_error(exc) from exc
    return RouteModeResponse(**receipt.__dict__)
