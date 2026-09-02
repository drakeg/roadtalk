import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import notifications as notifications_api
from app.api.auth import current_session
from app.auth.service import AuthenticatedSession
from app.config import Settings
from app.db.models import Account, Device, Session
from app.db.session import get_session
from app.main import create_app
from app.notifications.contracts import UrgentAlertNotificationPayload
from app.notifications.service import NotificationError, NotificationReceipt, PreferencesReceipt

NOW = datetime(2026, 9, 1, 12, tzinfo=UTC)


def settings() -> Settings:
    return Settings(
        environment="test", docs_enabled=True, log_level="CRITICAL", database_check_enabled=False
    )


def authenticated_application(*, account_type: str = "registered") -> FastAPI:
    application = create_app(settings())
    account = Account(id=uuid.uuid4(), account_type=account_type)
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="ios",
        installation_id="notification-route-synthetic",
    )
    session = Session(
        id=uuid.uuid4(),
        account=account,
        device=device,
        refresh_token_hash="notification-synthetic-hash",
        expires_at=NOW + timedelta(days=1),
    )
    current = AuthenticatedSession(account=account, device=device, session=session)
    db = cast(AsyncSession, MagicMock())

    async def override_current() -> AuthenticatedSession:
        return current

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield db

    application.dependency_overrides[current_session] = override_current
    application.dependency_overrides[get_session] = override_db
    return application


def notification_receipt(*, version: int = 1) -> NotificationReceipt:
    return NotificationReceipt(
        id=uuid.uuid4(),
        notification_class="channel_activity",
        priority="normal",
        source="roadtalk_channel",
        title="Channel activity",
        message="There is current activity on your selected channel.",
        channel_label="General",
        issued_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        read_at=None,
        dismissed_at=None,
        version=version,
        verified=None,
        emergency_service=None,
        delivery_guaranteed=None,
        safety_not_emergency_service=None,
        safety_delivery_not_guaranteed=None,
        safety_emergency_services_guidance=None,
        safety_unverified=None,
    )


def test_notification_openapi_is_authenticated_exact_and_non_disclosing() -> None:
    schema = create_app(settings()).openapi()
    paths = schema["paths"]
    for path, method in (
        ("/api/v1/me/notification-preferences", "get"),
        ("/api/v1/me/notification-preferences", "put"),
        ("/api/v1/me/notifications", "get"),
        ("/api/v1/me/notifications/{notification_id}/state", "put"),
        ("/api/v1/notifications/urgent-alerts", "post"),
    ):
        operation = paths[path][method]
        assert operation["security"] == [{"HTTPBearer": []}]
        assert operation["tags"] == ["notifications"]
    components = schema["components"]["schemas"]
    assert set(components["NotificationPreferencesUpdateRequest"]["properties"]) == {
        "channel_activity_enabled",
        "urgent_alert_enabled",
        "expected_version",
    }
    assert set(components["NotificationStateUpdateRequest"]["properties"]) == {
        "state",
        "expected_version",
    }
    assert set(components["UrgentAlertCommand"]["properties"]) == {"message", "idempotency_key"}
    exposed = str(
        {
            name: components[name]
            for name in (
                "NotificationPreferencesResponse",
                "NotificationRecordResponse",
                "NotificationInboxResponse",
                "UrgentAlertCommand",
                "UrgentAlertCommandResponse",
            )
        }
    ).lower()
    for forbidden in (
        "username",
        "password",
        "recovery_key",
        "push_token",
        "latitude",
        "longitude",
        "provider_ref",
        "recipient_id",
        "device_id",
        "radius_m",
        "corridor",
        "destination",
    ):
        assert forbidden not in exposed


def test_notification_routes_require_authentication() -> None:
    with TestClient(create_app(settings()), raise_server_exceptions=False) as client:
        responses = (
            client.get("/api/v1/me/notification-preferences"),
            client.get("/api/v1/me/notifications"),
            client.put(
                f"/api/v1/me/notifications/{uuid.uuid4()}/state",
                json={"state": "read", "expected_version": 1},
            ),
            client.post(
                "/api/v1/notifications/urgent-alerts",
                json={
                    "message": "Disabled vehicle ahead.",
                    "idempotency_key": "browser-route-key-1234",
                },
            ),
        )
    assert {response.status_code for response in responses} == {401}


def test_notification_preferences_and_inbox_use_semantic_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = notification_receipt()

    async def preferences(*args: object, **kwargs: object) -> PreferencesReceipt:
        return PreferencesReceipt(True, True, 1)

    async def update(*args: object, **kwargs: object) -> PreferencesReceipt:
        return PreferencesReceipt(False, True, 2)

    async def inbox(*args: object, **kwargs: object) -> tuple[NotificationReceipt, ...]:
        return (item,)

    async def state(*args: object, **kwargs: object) -> NotificationReceipt:
        return NotificationReceipt(**{**item.__dict__, "read_at": NOW, "version": 2})

    monkeypatch.setattr(notifications_api, "get_preferences", preferences)
    monkeypatch.setattr(notifications_api, "update_preferences", update)
    monkeypatch.setattr(notifications_api, "list_notifications", inbox)
    monkeypatch.setattr(notifications_api, "update_notification_state", state)
    with TestClient(authenticated_application()) as client:
        current = client.get("/api/v1/me/notification-preferences")
        changed = client.put(
            "/api/v1/me/notification-preferences",
            json={
                "channel_activity_enabled": False,
                "urgent_alert_enabled": True,
                "expected_version": 1,
            },
        )
        listed = client.get("/api/v1/me/notifications")
        marked = client.put(
            f"/api/v1/me/notifications/{item.id}/state",
            json={"state": "read", "expected_version": 1},
        )
    assert current.json() == {
        "channel_activity_enabled": True,
        "urgent_alert_enabled": True,
        "version": 1,
    }
    assert changed.json()["version"] == 2
    assert listed.json()["items"][0]["channel_label"] == "General"
    assert marked.json()["read_at"] == "2026-09-01T12:00:00Z"


def test_urgent_alert_command_uses_server_authorized_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def compose(*args: object, **kwargs: object) -> tuple[NotificationReceipt, ...]:
        captured.update(kwargs)
        return (notification_receipt(),)

    monkeypatch.setattr(notifications_api, "compose_authorized_notifications", compose)
    with TestClient(authenticated_application()) as client:
        response = client.post(
            "/api/v1/notifications/urgent-alerts",
            json={
                "message": "Disabled vehicle ahead.",
                "idempotency_key": "browser-route-key-1234",
            },
        )
    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert response.json()["recipient_count"] == 1
    payload = cast(UrgentAlertNotificationPayload, captured["payload"])
    assert payload.notification_class == "urgent_alert"
    assert payload.message == "Disabled vehicle ahead."
    assert "recipient" not in captured
    assert "radius" not in captured
    assert "location" not in captured


def test_urgent_alert_requires_registered_account() -> None:
    with TestClient(authenticated_application(account_type="anonymous")) as client:
        response = client.post(
            "/api/v1/notifications/urgent-alerts",
            json={
                "message": "Disabled vehicle ahead.",
                "idempotency_key": "browser-route-key-1234",
            },
        )
    assert response.status_code == 403
    assert response.json()["code"] == "REGISTERED_ACCOUNT_REQUIRED"


def test_notification_routes_reject_overposting_and_conflicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def reject(*args: object, **kwargs: object) -> PreferencesReceipt:
        raise NotificationError(
            "NOTIFICATION_PREFERENCES_VERSION_CONFLICT",
            "Notification preferences changed; reload them before retrying.",
        )

    monkeypatch.setattr(notifications_api, "update_preferences", reject)
    with TestClient(authenticated_application()) as client:
        overposted = client.put(
            "/api/v1/me/notification-preferences",
            json={
                "channel_activity_enabled": True,
                "urgent_alert_enabled": True,
                "expected_version": 1,
                "marketing_enabled": True,
            },
        )
        conflict = client.put(
            "/api/v1/me/notification-preferences",
            json={
                "channel_activity_enabled": True,
                "urgent_alert_enabled": True,
                "expected_version": 1,
            },
        )
        targeted = client.post(
            "/api/v1/notifications/urgent-alerts",
            json={
                "message": "Help",
                "idempotency_key": "browser-route-key-1234",
                "recipient_id": str(uuid.uuid4()),
            },
        )
    assert overposted.status_code == 422
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "NOTIFICATION_PREFERENCES_VERSION_CONFLICT"
    assert targeted.status_code == 422
