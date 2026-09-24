import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.auth import CurrentSession, DatabaseSession
from app.convoys.awareness import current_convoy_awareness
from app.convoys.contracts import ConvoyAwarenessSnapshot
from app.convoys.service import (
    ConvoyLifecycleError,
    create_convoy,
    disband_convoy,
    end_membership,
    join_convoy,
)
from app.db.models import Convoy, ConvoyMembership

router = APIRouter(prefix="/api/v1/convoys", tags=["convoys"])


class ClosedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateConvoyRequest(ClosedRequest):
    display_name: str = Field(min_length=1, max_length=64)


class JoinConvoyRequest(ClosedRequest):
    convoy_id: uuid.UUID


class ConvoyStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    convoy_id: uuid.UUID
    membership_id: uuid.UUID
    display_name: str
    role: Literal["leader", "member"]
    state: Literal["active"] = "active"


def _conflict(exc: ConvoyLifecycleError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "CONVOY_LIFECYCLE_CONFLICT", "detail": "Convoy state changed or is unavailable."},
    )


async def _status(db: DatabaseSession, account_id: uuid.UUID) -> ConvoyStatusResponse | None:
    row = (
        await db.execute(
            select(Convoy, ConvoyMembership)
            .join(ConvoyMembership, ConvoyMembership.convoy_id == Convoy.id)
            .where(
                ConvoyMembership.account_id == account_id,
                ConvoyMembership.state == "active",
                Convoy.state == "active",
            )
        )
    ).one_or_none()
    if row is None:
        return None
    convoy, membership = row
    return ConvoyStatusResponse(
        convoy_id=convoy.id,
        membership_id=membership.id,
        display_name=convoy.display_name,
        role=membership.role,
    )


@router.get("/me", response_model=ConvoyStatusResponse | None)
async def read_convoy_status(
    db: DatabaseSession, current: CurrentSession
) -> ConvoyStatusResponse | None:
    return await _status(db, current.account.id)


@router.post("", response_model=ConvoyStatusResponse, status_code=status.HTTP_201_CREATED)
async def create_current_convoy(
    payload: CreateConvoyRequest, db: DatabaseSession, current: CurrentSession
) -> ConvoyStatusResponse:
    if await _status(db, current.account.id) is not None:
        raise HTTPException(status_code=409, detail={"code": "CONVOY_ALREADY_ACTIVE"})
    try:
        convoy, membership = await create_convoy(
            db, leader=current.account, display_name=payload.display_name
        )
    except ConvoyLifecycleError as exc:
        raise _conflict(exc) from exc
    return ConvoyStatusResponse(
        convoy_id=convoy.id,
        membership_id=membership.id,
        display_name=convoy.display_name,
        role="leader",
    )


@router.post("/join", response_model=ConvoyStatusResponse)
async def join_current_convoy(
    payload: JoinConvoyRequest, db: DatabaseSession, current: CurrentSession
) -> ConvoyStatusResponse:
    if await _status(db, current.account.id) is not None:
        raise HTTPException(status_code=409, detail={"code": "CONVOY_ALREADY_ACTIVE"})
    try:
        membership = await join_convoy(db, convoy_id=payload.convoy_id, account=current.account)
    except ConvoyLifecycleError as exc:
        raise _conflict(exc) from exc
    convoy = await db.get(Convoy, membership.convoy_id)
    if convoy is None:
        raise HTTPException(status_code=409, detail={"code": "CONVOY_UNAVAILABLE"})
    return ConvoyStatusResponse(
        convoy_id=convoy.id,
        membership_id=membership.id,
        display_name=convoy.display_name,
        role="member",
    )


@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_current_convoy(db: DatabaseSession, current: CurrentSession) -> None:
    current_status = await _status(db, current.account.id)
    if current_status is None or current_status.role == "leader":
        raise HTTPException(status_code=409, detail={"code": "CONVOY_LEAVE_UNAVAILABLE"})
    try:
        await end_membership(
            db,
            membership_id=current_status.membership_id,
            account_id=current.account.id,
            state="left",
        )
    except ConvoyLifecycleError as exc:
        raise _conflict(exc) from exc


@router.post("/disband", status_code=status.HTTP_204_NO_CONTENT)
async def disband_current_convoy(db: DatabaseSession, current: CurrentSession) -> None:
    current_status = await _status(db, current.account.id)
    if current_status is None or current_status.role != "leader":
        raise HTTPException(status_code=409, detail={"code": "CONVOY_DISBAND_UNAVAILABLE"})
    try:
        await disband_convoy(
            db,
            convoy_id=current_status.convoy_id,
            leader_account_id=current.account.id,
        )
    except ConvoyLifecycleError as exc:
        raise _conflict(exc) from exc


@router.get("/awareness", response_model=ConvoyAwarenessSnapshot | None)
async def read_convoy_awareness(
    request: Request, db: DatabaseSession, current: CurrentSession
) -> ConvoyAwarenessSnapshot | None:
    return await current_convoy_awareness(
        db,
        viewer_account_id=current.account.id,
        location_policy_version=request.app.state.settings.location_policy_version,
    )
