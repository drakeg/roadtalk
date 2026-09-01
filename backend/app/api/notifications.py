import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.auth import CurrentSession, DatabaseSession
from app.notifications.schemas import (
    NotificationInboxResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdateRequest,
    NotificationRecordResponse,
    NotificationStateUpdateRequest,
)
from app.notifications.service import (
    NotificationError,
    get_preferences,
    list_notifications,
    update_notification_state,
    update_preferences,
)

router = APIRouter(prefix="/api/v1", tags=["notifications"])


def _notification_error(exc: NotificationError) -> HTTPException:
    status_code = (
        status.HTTP_409_CONFLICT
        if exc.code.endswith("VERSION_CONFLICT")
        else status.HTTP_404_NOT_FOUND
    )
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "detail": exc.detail},
    )


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
