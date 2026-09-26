import time
import uuid
from typing import cast

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.api.auth import CurrentSession, DatabaseSession
from app.db.models import ModerationRestriction
from app.moderation.contracts import (
    ReportCommand,
    ReportSummary,
    RestrictionCommand,
    RestrictionKind,
)
from app.moderation.limiter import ModerationRateLimitError, ModerationReportLimiter
from app.moderation.service import (
    ReportLifecycleError,
    RestrictionLifecycleError,
    revoke_restriction,
    set_restriction,
    submit_report,
)

router = APIRouter(prefix="/api/v1/moderation", tags=["moderation"])


class RestrictionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restriction_id: uuid.UUID
    subject_account_id: uuid.UUID
    kind: RestrictionKind


class RestrictionList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: tuple[RestrictionSummary, ...]


def _unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "MODERATION_UNAVAILABLE", "detail": "Moderation action is unavailable."},
    )


@router.post("/reports", response_model=ReportSummary, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: Request,
    payload: ReportCommand,
    db: DatabaseSession,
    current: CurrentSession,
) -> ReportSummary:
    limiter = cast(ModerationReportLimiter, request.app.state.moderation_report_limiter)
    peer = request.client.host if request.client is not None else "unknown"
    try:
        limiter.check(
            peer=peer,
            account_id=str(current.account.id),
            device_id=str(current.device.id),
            event_key=payload.idempotency_key,
            now=time.monotonic(),
        )
    except ModerationRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "MODERATION_RATE_LIMITED",
                "detail": "Moderation action is unavailable.",
            },
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    try:
        report = await submit_report(
            db,
            reporter=current.account,
            subject_account_id=payload.subject_account_id,
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
        )
    except ReportLifecycleError as exc:
        raise _unavailable() from exc
    return ReportSummary(
        report_id=report.id,
        subject_account_id=report.subject_account_id,
        reason=report.reason,
        state=report.state,
        created_at=report.created_at,
    )


@router.get("/restrictions", response_model=RestrictionList)
async def list_restrictions(db: DatabaseSession, current: CurrentSession) -> RestrictionList:
    rows = (
        await db.scalars(
            select(ModerationRestriction).where(
                ModerationRestriction.actor_account_id == current.account.id,
                ModerationRestriction.state == "active",
            )
        )
    ).all()
    return RestrictionList(
        items=tuple(
            RestrictionSummary(
                restriction_id=row.id,
                subject_account_id=row.subject_account_id,
                kind=row.kind,
            )
            for row in rows
        )
    )


@router.post("/restrictions", response_model=RestrictionSummary)
async def create_restriction(
    payload: RestrictionCommand,
    db: DatabaseSession,
    current: CurrentSession,
) -> RestrictionSummary:
    try:
        row = await set_restriction(
            db,
            actor=current.account,
            subject_account_id=payload.subject_account_id,
            kind=payload.kind,
        )
    except RestrictionLifecycleError as exc:
        raise _unavailable() from exc
    return RestrictionSummary(
        restriction_id=row.id,
        subject_account_id=row.subject_account_id,
        kind=row.kind,
    )


@router.delete("/restrictions/{restriction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restriction(
    restriction_id: uuid.UUID,
    db: DatabaseSession,
    current: CurrentSession,
) -> None:
    try:
        await revoke_restriction(
            db,
            actor_account_id=current.account.id,
            restriction_id=restriction_id,
        )
    except RestrictionLifecycleError as exc:
        raise _unavailable() from exc
