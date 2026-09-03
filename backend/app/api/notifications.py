import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

from fastapi import APIRouter, HTTPException, Request, status

from app.api.auth import CurrentSession, DatabaseSession
from app.notifications.contracts import (
    URGENT_ALERT_MAX_TTL,
    UrgentAlertCommand,
    UrgentAlertNotificationPayload,
)
from app.notifications.limiter import UrgentAlertLimiter, UrgentAlertRateLimitError
from app.notifications.schemas import (
    NotificationInboxResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdateRequest,
    NotificationRecordResponse,
    NotificationStateUpdateRequest,
    UrgentAlertCommandResponse,
)
from app.notifications.service import (
    NotificationError,
    compose_authorized_notifications,
    get_preferences,
    list_notifications,
    update_notification_state,
    update_preferences,
)

router = APIRouter(prefix="/api/v1", tags=["notifications"])


def _notification_error(exc: NotificationError) -> HTTPException:
    status_code = (
        status.HTTP_409_CONFLICT
        if exc.code.endswith("VERSION_CONFLICT") or exc.code.endswith("IDEMPOTENCY_CONFLICT")
        else status.HTTP_404_NOT_FOUND
    )
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "detail": exc.detail},
    )


def _check_urgent_alert_limit(
    request: Request,
    current: CurrentSession,
    *,
    event_key: str,
) -> None:
    limiter = cast(UrgentAlertLimiter, request.app.state.urgent_alert_limiter)
    peer = request.client.host if request.client is not None else "unknown"
    try:
        limiter.check(
            peer=peer,
            account_id=str(current.account.id),
            device_id=str(current.device.id),
            event_key=event_key,
            now=time.monotonic(),
        )
    except UrgentAlertRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "URGENT_ALERT_RATE_LIMITED",
                "detail": "Urgent alert is temporarily unavailable.",
            },
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


@router.get(
    "/me/notification-preferences",
    response_model=NotificationPreferencesResponse,
)
async def read_notification_preferences(
    db: DatabaseSession, current: CurrentSession
) -> NotificationPreferencesResponse:
    try:
        receipt = await get_preferences(db, account_id=current.account.id)
    except NotificationError as exc:
        raise _notification_error(exc) from exc
    return NotificationPreferencesResponse(**receipt.__dict__)


@router.put(
    "/me/notification-preferences",
    response_model=NotificationPreferencesResponse,
)
async def write_notification_preferences(
    payload: NotificationPreferencesUpdateRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> NotificationPreferencesResponse:
    try:
        receipt = await update_preferences(
            db,
            account_id=current.account.id,
            channel_activity_enabled=payload.channel_activity_enabled,
            urgent_alert_enabled=payload.urgent_alert_enabled,
            expected_version=payload.expected_version,
        )
    except NotificationError as exc:
        raise _notification_error(exc) from exc
    return NotificationPreferencesResponse(**receipt.__dict__)


@router.get("/me/notifications", response_model=NotificationInboxResponse)
async def read_notifications(
    db: DatabaseSession, current: CurrentSession
) -> NotificationInboxResponse:
    try:
        receipts = await list_notifications(db, account_id=current.account.id)
    except NotificationError as exc:
        raise _notification_error(exc) from exc
    return NotificationInboxResponse(
        items=tuple(NotificationRecordResponse(**receipt.__dict__) for receipt in receipts)
    )


@router.put(
    "/me/notifications/{notification_id}/state",
    response_model=NotificationRecordResponse,
)
async def write_notification_state(
    notification_id: uuid.UUID,
    payload: NotificationStateUpdateRequest,
    db: DatabaseSession,
    current: CurrentSession,
) -> NotificationRecordResponse:
    try:
        receipt = await update_notification_state(
            db,
            account_id=current.account.id,
            notification_id=notification_id,
            state=payload.state,
            expected_version=payload.expected_version,
        )
    except NotificationError as exc:
        raise _notification_error(exc) from exc
    return NotificationRecordResponse(**receipt.__dict__)


@router.post("/notifications/urgent-alerts", response_model=UrgentAlertCommandResponse)
async def create_urgent_alert(
    request: Request,
    payload: UrgentAlertCommand,
    db: DatabaseSession,
    current: CurrentSession,
) -> UrgentAlertCommandResponse:
    if current.account.account_type != "registered":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "REGISTERED_ACCOUNT_REQUIRED",
                "detail": "A persistent registered account is required to send an urgent alert.",
            },
        )
    _check_urgent_alert_limit(request, current, event_key=payload.idempotency_key)
    now = datetime.now(UTC)
    event = UrgentAlertNotificationPayload(
        message=payload.message,
        issued_at=now,
        expires_at=now + min(URGENT_ALERT_MAX_TTL, timedelta(minutes=10)),
    )
    try:
        receipts = await compose_authorized_notifications(
            db,
            sender_account_id=current.account.id,
            sender_device_id=current.device.id,
            payload=event,
            idempotency_key=payload.idempotency_key,
            settings=request.app.state.settings,
            now=now,
        )
    except NotificationError as exc:
        raise _notification_error(exc) from exc
    return UrgentAlertCommandResponse(
        accepted=True,
        recipient_count=len(receipts),
        issued_at=event.issued_at,
        expires_at=event.expires_at,
    )
