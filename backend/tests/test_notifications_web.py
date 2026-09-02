from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def client() -> TestClient:
    return TestClient(
        create_app(
            Settings(
                environment="test",
                docs_enabled=False,
                log_level="CRITICAL",
                database_check_enabled=False,
            )
        ),
        raise_server_exceptions=False,
    )


def test_notifications_page_exposes_in_app_account_owned_experience() -> None:
    with client() as test_client:
        response = test_client.get("/notifications")

    assert response.status_code == 200
    assert "RoadTalk Notifications" in response.text
    assert "/api/v1/me/notification-preferences" in response.text
    assert "/api/v1/me/notifications" in response.text
    assert "/api/v1/notifications/urgent-alerts" in response.text
    assert "persistent registered account" in response.text
    assert "Browser push is not active" in response.text
    assert 'role="status" aria-live="polite"' in response.text


def test_notifications_page_locks_urgent_alert_safety_and_targeting_copy() -> None:
    with client() as test_client:
        response = test_client.get("/notifications")

    assert response.status_code == 200
    html = response.text
    assert "RoadTalk is not an emergency service. Delivery is not guaranteed." in html
    assert "user-generated and unverified" in html
    assert "Contact local emergency services directly" in html
    assert "You cannot target a person, location, radius, route, or destination." in html
    assert "delivery/read/response is not guaranteed" in html
    assert "recipient_id" not in html
    assert "device_id" not in html
    assert "latitude" not in html
    assert "longitude" not in html
    assert "radius_m" not in html


def test_radio_and_account_navigation_include_notifications() -> None:
    with client() as test_client:
        radio = test_client.get("/")
        account = test_client.get("/account")
        ops = test_client.get("/ops")

    assert 'href="/notifications">Notifications</a>' in radio.text
    assert 'href="/notifications">Notifications</a>' in account.text
    assert 'href="/notifications">Notifications</a>' in ops.text
