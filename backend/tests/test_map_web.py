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


def test_browser_map_exposes_privacy_safe_awareness_surface() -> None:
    with client() as test_client:
        response = test_client.get("/map")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "RoadTalk | Map Awareness" in response.text
    assert 'role="img" aria-label="RoadTalk awareness map"' in response.text
    assert "/api/v1/presence/nearby" in response.text
    assert "privacy_min_accounts!==3" in response.text
    assert "cell.cell_size_m!==2000" in response.text
    assert "No public map, tile, geocoding, routing, or traffic service is contacted." in response.text
    assert "Your exact position is shown only to you on this page." in response.text


def test_browser_map_has_actionable_secure_context_and_location_diagnostics() -> None:
    with client() as test_client:
        response = test_client.get("/map")

    assert response.status_code == 200
    assert "window.isSecureContext" in response.text
    assert "navigator.geolocation.getCurrentPosition" in response.text
    assert "http://127.0.0.1" in response.text
    assert "RoadTalk HTTPS LAN gateway" in response.text
    assert "operating-system location service" in response.text
    assert "background" not in response.text.lower()


def test_browser_map_rejects_disclosing_presence_fields_before_rendering() -> None:
    with client() as test_client:
        response = test_client.get("/map")

    assert response.status_code == 200
    for field in (
        "account_id",
        "device_id",
        "identity",
        "callsign",
        "exact_count",
        "distance_m",
        "bearing",
        "heading",
        "speed",
        "route",
        "corridor",
        "direction",
        "destination",
        "history",
    ):
        assert f"'{field}'" in response.text
    assert "Presence response crossed the browser privacy boundary" in response.text


def test_browser_navigation_connects_radio_map_audience_and_operations() -> None:
    with client() as test_client:
        radio = test_client.get("/")
        map_page = test_client.get("/map")
        audience = test_client.get("/audience")
        operations = test_client.get("/ops")

    assert 'href="/map">Map</a>' in radio.text
    for target in ('href="/">Web Radio</a>', 'href="/audience">Audience</a>', 'href="/ops">Operations</a>'):
        assert target in map_page.text
    assert 'href="/map">Map</a>' in audience.text
    assert 'href="/map">Map Awareness</a>' in operations.text
