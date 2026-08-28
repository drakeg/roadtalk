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
    marker = '<script id="roadtalk-browser-hardening">'
    assert marker in html
    hardening = html[html.index(marker) :]
    assert "state.refresh = localStorage.getItem('rt_refresh')" in hardening
    assert "if (state.refresh)" in hardening
    assert "if (await refresh())" in hardening
    assert "await api('/api/v1/auth/session')" in hardening
    assert hardening.index("if (await refresh())") < hardening.index(
        "fetch('/api/v1/auth/anonymous'"
    )
    assert "DEVICE_ALREADY_REGISTERED" in hardening
    assert "saved session could not be recovered" in hardening


def test_web_radio_keeps_guest_reset_as_explicit_account_aware_fallback() -> None:
    with client() as test_client:
        response = test_client.get("/")

    assert response.status_code == 200
    html = response.text
    marker = '<script id="roadtalk-browser-hardening">'
    hardening = html[html.index(marker) :]
    assert "window.confirm(" in hardening
    assert "Press OK to start a new guest identity" in hardening
    assert "Cancel and use Account to log in to your persistent RoadTalk account" in hardening
    assert "localStorage.removeItem('rt_access')" in hardening
    assert "localStorage.removeItem('rt_refresh')" in hardening
    assert "localStorage.removeItem('rt_install')" in hardening
    assert "localStorage.removeItem('rt_location_seq')" in hardening
    assert "return recoverBrowserSession(false)" in hardening


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
