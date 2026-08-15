import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from app.api.auth import CurrentSession, DatabaseSession
from app.channels.limiter import ChannelRateLimitError
from app.channels.schemas import (
    ChannelCatalogResponse,
    ChannelLifecycleResponse,
    ChannelSelectionResponse,
    ChannelSummaryResponse,
    PrivateChannelCreateRequest,
    PrivateChannelInviteResponse,
    PrivateChannelJoinRequest,
)
from app.channels.service import (
    ChannelError,
    close_private_channel,
    create_private_channel,
    get_current_channel,
    join_private_channel,
    leave_private_channel,
    list_channels,
    rotate_private_invite,
    select_channel,
)

router = APIRouter(prefix="/api/v1", tags=["channels"])
IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=16,
        max_length=128,
        pattern=r"^[A-Za-z0-9._~-]+$",
    ),
]


def _channel_error(exc: ChannelError) -> HTTPException:
    status_code = status.HTTP_409_CONFLICT
    if exc.code == "CHANNEL_NOT_AVAILABLE":
        status_code = status.HTTP_404_NOT_FOUND
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "detail": exc.detail},
    )


def _check_invite_limit(request: Request, current: CurrentSession) -> None:
    peer = request.client.host if request.client else "unknown"
    try:
        request.app.state.channel_invite_limiter.check(
            peer=peer, account_id=str(current.account.id), now=time.monotonic()
        )
    except ChannelRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "CHANNEL_INVITE_LIMITED", "detail": str(exc)},
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


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


@router.post(
    "/channels/private",
    response_model=PrivateChannelInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_private(
    request: Request,
    response: Response,
    payload: PrivateChannelCreateRequest,
    idempotency_key: IdempotencyKey,
    db: DatabaseSession,
    current: CurrentSession,
) -> PrivateChannelInviteResponse:
    try:
        receipt = await create_private_channel(
            db,
            account_id=current.account.id,
            display_label=payload.display_label,
            idempotency_key=idempotency_key,
            settings=request.app.state.settings,
        )
    except ChannelError as exc:
        raise _channel_error(exc) from exc
    if receipt.replayed:
        response.status_code = status.HTTP_200_OK
    return PrivateChannelInviteResponse(**receipt.__dict__)


@router.post("/channels/private/join", response_model=ChannelLifecycleResponse)
async def join_private(
    request: Request,
    payload: PrivateChannelJoinRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> ChannelLifecycleResponse:
    _check_invite_limit(request, current)
    try:
        receipt = await join_private_channel(
            db,
            account_id=current.account.id,
            raw_invite=payload.invite,
            settings=request.app.state.settings,
        )
    except ChannelError as exc:
        raise _channel_error(exc) from exc
    return ChannelLifecycleResponse(**receipt.__dict__)


@router.delete("/channels/{channel_id}/membership", response_model=ChannelLifecycleResponse)
async def leave_private(
    channel_id: uuid.UUID, db: DatabaseSession, current: CurrentSession
) -> ChannelLifecycleResponse:
    try:
        receipt = await leave_private_channel(
            db, account_id=current.account.id, channel_id=channel_id
        )
    except ChannelError as exc:
        raise _channel_error(exc) from exc
    return ChannelLifecycleResponse(**receipt.__dict__)


@router.post(
    "/channels/{channel_id}/invite/rotation",
    response_model=PrivateChannelInviteResponse,
)
async def rotate_invite(
    channel_id: uuid.UUID,
    request: Request,
    idempotency_key: IdempotencyKey,
    db: DatabaseSession,
    current: CurrentSession,
) -> PrivateChannelInviteResponse:
    try:
        receipt = await rotate_private_invite(
            db,
            account_id=current.account.id,
            channel_id=channel_id,
            idempotency_key=idempotency_key,
            settings=request.app.state.settings,
        )
    except ChannelError as exc:
        raise _channel_error(exc) from exc
    return PrivateChannelInviteResponse(**receipt.__dict__)


@router.delete("/channels/{channel_id}", response_model=ChannelLifecycleResponse)
async def close_private(
    channel_id: uuid.UUID, db: DatabaseSession, current: CurrentSession
) -> ChannelLifecycleResponse:
    try:
        receipt = await close_private_channel(
            db, account_id=current.account.id, channel_id=channel_id
        )
    except ChannelError as exc:
        raise _channel_error(exc) from exc
    return ChannelLifecycleResponse(**receipt.__dict__)
