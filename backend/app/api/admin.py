import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.admin.service import (
    AdminAccountList,
    AdminAuthorizationError,
    AdminMutationError,
    AdminMutationRequest,
    AdminMutationResponse,
    list_accounts,
    require_admin,
    revoke_account_sessions,
    set_account_enabled,
)
from app.api.auth import CurrentSession, DatabaseSession

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _authorize(current: CurrentSession) -> None:
    try:
        require_admin(current)
    except AdminAuthorizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_REQUIRED", "detail": str(exc)},
        ) from exc


def _mutation_error(exc: AdminMutationError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "ADMIN_MUTATION_REJECTED", "detail": str(exc)},
    )


@router.get("/accounts", response_model=AdminAccountList)
async def admin_accounts(
    db: DatabaseSession,
    current: CurrentSession,
    q: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=50, ge=1, le=100),
) -> AdminAccountList:
    _authorize(current)
    return await list_accounts(db, query=q, limit=limit)


@router.post("/accounts/{account_id}/disable", response_model=AdminMutationResponse)
async def disable_account(
    account_id: uuid.UUID,
    payload: AdminMutationRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> AdminMutationResponse:
    _authorize(current)
    try:
        return await set_account_enabled(
            db,
            actor=current,
            target_account_id=account_id,
            enabled=False,
            confirmed=payload.confirm,
        )
    except AdminMutationError as exc:
        raise _mutation_error(exc) from exc


@router.post("/accounts/{account_id}/enable", response_model=AdminMutationResponse)
async def enable_account(
    account_id: uuid.UUID,
    payload: AdminMutationRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> AdminMutationResponse:
    _authorize(current)
    try:
        return await set_account_enabled(
            db,
            actor=current,
            target_account_id=account_id,
            enabled=True,
            confirmed=payload.confirm,
        )
    except AdminMutationError as exc:
        raise _mutation_error(exc) from exc


@router.post("/accounts/{account_id}/revoke-sessions", response_model=AdminMutationResponse)
async def revoke_sessions(
    account_id: uuid.UUID,
    payload: AdminMutationRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> AdminMutationResponse:
    _authorize(current)
    try:
        return await revoke_account_sessions(
            db,
            actor=current,
            target_account_id=account_id,
            confirmed=payload.confirm,
        )
    except AdminMutationError as exc:
        raise _mutation_error(exc) from exc
