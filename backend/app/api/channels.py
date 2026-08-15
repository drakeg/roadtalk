import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.auth import CurrentSession, DatabaseSession
from app.channels.schemas import (
    ChannelCatalogResponse,
    ChannelSelectionResponse,
    ChannelSummaryResponse,
)
from app.channels.service import (
    ChannelError,
    get_current_channel,
    list_channels,
    select_channel,
)

router = APIRouter(prefix="/api/v1", tags=["channels"])


def _channel_error(exc: ChannelError) -> HTTPException:
    status_code = status.HTTP_409_CONFLICT
    if exc.code == "CHANNEL_NOT_AVAILABLE":
        status_code = status.HTTP_404_NOT_FOUND
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "detail": exc.detail},
    )


@router.get("/channels", response_model=ChannelCatalogResponse)
async def read_channel_catalog(
    db: DatabaseSession,
    current: CurrentSession,
) -> ChannelCatalogResponse:
    try:
        channels = await list_channels(db, account_id=current.account.id)
    except ChannelError as exc:
        raise _channel_error(exc) from exc
    return ChannelCatalogResponse(
        items=tuple(ChannelSummaryResponse(**channel.__dict__) for channel in channels)
    )


@router.get("/me/channel", response_model=ChannelSelectionResponse)
async def read_current_channel(
    db: DatabaseSession,
    current: CurrentSession,
) -> ChannelSelectionResponse:
    try:
        selected = await get_current_channel(db, account_id=current.account.id)
    except ChannelError as exc:
        raise _channel_error(exc) from exc
    return ChannelSelectionResponse(**selected.__dict__)


@router.post("/channels/{channel_id}/select", response_model=ChannelSelectionResponse)
async def select_current_channel(
    channel_id: uuid.UUID,
    db: DatabaseSession,
    current: CurrentSession,
) -> ChannelSelectionResponse:
    try:
        selected = await select_channel(
            db,
            account_id=current.account.id,
            channel_id=channel_id,
        )
    except ChannelError as exc:
        raise _channel_error(exc) from exc
    return ChannelSelectionResponse(**selected.__dict__)
