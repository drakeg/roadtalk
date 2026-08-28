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


def test_web_radio_includes_permission_preflight_and_navigation() -> None:
    with client() as test_client:
        response = test_client.get("/")

    assert response.status_code == 200
    assert 'id="roadtalk-browser-hardening"' in response.text
    assert "window.isSecureContext" in response.text
    assert "navigator.mediaDevices.getUserMedia" in response.text
    assert "enableHighAccuracy: true" in response.text
    assert "enableHighAccuracy: false" in response.text
    assert "maximumAge: 60000" in response.text
    assert "event.stopImmediatePropagation()" in response.text
    assert "await microphonePreflight()" in response.text
    assert "await locationPreflight()" in response.text
    assert 'href="/audience">Audience</a>' in response.text


def test_web_radio_recovers_stale_access_with_saved_refresh_before_registering() -> None:
    with client() as test_client:
        response = test_client.get("/")

    assert response.status_code == 200
    html = response.text
    assert "state.refresh = localStorage.getItem('rt_refresh')" in html
    assert "if (state.refresh)" in html
    assert "if (await refresh())" in html
    assert "await api('/api/v1/auth/session')" in html
    assert html.index("if (await refresh())") < html.index("fetch('/api/v1/auth/anonymous'")
    assert "DEVICE_ALREADY_REGISTERED" in html
    assert "saved session could not be recovered" in html


def test_operations_dashboard_links_back_to_user_pages() -> None:
    with client() as test_client:
        response = test_client.get("/ops")

    assert response.status_code == 200
    assert 'href="/">Web Radio</a>' in response.text
    assert 'href="/audience">Audience Mode</a>' in response.text


def test_permission_copy_explains_secure_lan_requirement() -> None:
    with client() as test_client:
        response = test_client.get("/")

    assert response.status_code == 200
    assert "Browser microphone and location require a secure origin" in response.text
    assert "http://127.0.0.1" in response.text
    assert "RoadTalk HTTPS LAN gateway" in response.text
    assert "Microphone permission is blocked" in response.text
    assert "operating-system location service" in response.text
