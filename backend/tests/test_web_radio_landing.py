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


def test_desktop_web_radio_explains_product_before_console() -> None:
    with client() as test_client:
        response = test_client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'class="desktop-welcome"' in html
    assert "The familiar feel of CB radio, built for connected travelers." in html
    assert "Nearby conversations" in html
    assert "Your call sign follows you" in html
    assert "Awareness, not tracking" in html
    assert "How it works" in html
    assert 'href="#radio-console">Open the radio</a>' in html
    assert 'href="/account">Manage your account</a>' in html
    assert 'id="radio-console" class="grid"' in html


def test_desktop_welcome_preserves_mobile_radio_priority() -> None:
    with client() as test_client:
        response = test_client.get("/")

    assert response.status_code == 200
    html = response.text
    assert ".desktop-welcome{display:none}" in html
    assert "@media(min-width:851px)" in html
    assert "#radio-console .ptt{width:230px}" in html
    assert 'id="ptt" class="ptt" disabled' in html


def test_desktop_landing_preserves_browser_hardening() -> None:
    with client() as test_client:
        response = test_client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="roadtalk-browser-hardening"' in html
    assert "window.isSecureContext" in html
    assert "await microphonePreflight()" in html
    assert "await locationPreflight()" in html
    assert "location.replace('/account')" in html
