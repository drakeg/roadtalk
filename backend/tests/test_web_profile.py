from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def settings() -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
    )


def test_web_profile_page_exposes_avatar_and_callsign_controls() -> None:
    with TestClient(create_app(settings())) as client:
        response = client.get("/profile")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="callsign"' in response.text
    assert 'id="avatars"' in response.text
    assert 'id="save"' in response.text
    assert "/api/v1/me/profile" in response.text
    assert "/api/v1/avatars" in response.text
    assert "/api/v1/callsigns/availability" in response.text
    assert 'href="/"' in response.text


def test_web_profile_page_does_not_expand_openapi_contract() -> None:
    schema = create_app(settings()).openapi()

    assert "/profile" not in schema["paths"]
