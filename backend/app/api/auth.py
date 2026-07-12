import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    AnonymousSessionRequest,
    AnonymousSessionResponse,
    DeviceRevocationResponse,
    LogoutResponse,
    RefreshRequest,
    SessionIdentity,
    TokenPair,
)
from app.auth.security import AccessTokenError, decode_access_token
from app.auth.service import (
    AuthenticatedSession,
    AuthenticationError,
    authenticate_session,
    create_anonymous_session,
    revoke_device_sessions,
    revoke_session,
    rotate_refresh_token,
)
from app.config import Settings
from app.db.session import get_session

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
bearer = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


def auth_error(exc: AuthenticationError, status_code: int = 401) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "detail": exc.detail},
        headers={"WWW-Authenticate": "Bearer"} if status_code == 401 else None,
    )


async def current_session(
    request: Request,
    db: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthenticatedSession:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_REQUIRED", "detail": "Bearer token is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings: Settings = request.app.state.settings
    try:
        claims = decode_access_token(credentials.credentials, settings)
        return await authenticate_session(
            db,
            account_id=uuid.UUID(claims["sub"]),
            device_id=uuid.UUID(claims["device_id"]),
            session_id=uuid.UUID(claims["session_id"]),
        )
    except (AccessTokenError, AuthenticationError, KeyError, ValueError) as exc:
        detail = exc.detail if isinstance(exc, AuthenticationError) else str(exc)
        code = exc.code if isinstance(exc, AuthenticationError) else "INVALID_ACCESS_TOKEN"
        raise auth_error(AuthenticationError(code, detail)) from exc


CurrentSession = Annotated[AuthenticatedSession, Depends(current_session)]


@router.post(
    "/anonymous",
    response_model=AnonymousSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_anonymous(
    request: Request, payload: AnonymousSessionRequest, db: DatabaseSession
) -> AnonymousSessionResponse:
    try:
        return await create_anonymous_session(db, payload, request.app.state.settings)
    except AuthenticationError as exc:
        raise auth_error(exc, status.HTTP_409_CONFLICT) from exc


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    request: Request, payload: RefreshRequest, db: DatabaseSession
) -> TokenPair:
    try:
        return await rotate_refresh_token(db, payload.refresh_token, request.app.state.settings)
    except AuthenticationError as exc:
        raise auth_error(exc) from exc


@router.get("/session", response_model=SessionIdentity)
async def session_identity(current: CurrentSession) -> SessionIdentity:
    return SessionIdentity(
        account_id=current.account.id,
        device_id=current.device.id,
        session_id=current.session.id,
        account_type=current.account.account_type,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(db: DatabaseSession, current: CurrentSession) -> LogoutResponse:
    await revoke_session(db, current.session, "logout")
    return LogoutResponse()


@router.delete("/devices/{device_id}", response_model=DeviceRevocationResponse)
async def revoke_device(
    device_id: uuid.UUID, db: DatabaseSession, current: CurrentSession
) -> DeviceRevocationResponse:
    try:
        count = await revoke_device_sessions(
            db, account_id=current.account.id, device_id=device_id
        )
    except AuthenticationError as exc:
        raise auth_error(exc, status.HTTP_404_NOT_FOUND) from exc
    return DeviceRevocationResponse(device_id=device_id, revoked_sessions=count)
