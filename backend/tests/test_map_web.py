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
    assert 'role="img" aria-label="RoadTalk awareness map;' in response.text
    assert "/api/v1/presence/nearby" in response.text
    assert "privacy_min_accounts!==3" in response.text
    assert "cell.cell_size_m!==2000" in response.text
    assert (
        "No public map, tile, geocoding, routing, or traffic service is contacted." in response.text
    )
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
    lowered = response.text.lower()
    assert "background location" not in lowered
    assert "background tracking" not in lowered


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


def test_browser_map_has_keyboard_and_screen_reader_equivalent_awareness() -> None:
    with client() as test_client:
        response = test_client.get("/map")

    assert response.status_code == 200
    assert 'id="summary-title">Text awareness summary' in response.text
    assert 'role="status" aria-live="polite" aria-atomic="true"' in response.text
    assert 'role="alert"' in response.text
    assert 'aria-describedby="summary-text"' in response.text
    assert 'nav aria-label="RoadTalk"' in response.text
    assert ":focus-visible" in response.text
    assert "setSummary(data.cells.length?" in response.text
    assert "precision is limited to a 2 km privacy cell" in response.text


def test_browser_map_degraded_states_hide_prior_presence_and_false_precision() -> None:
    with client() as test_client:
        response = test_client.get("/map")

    assert response.status_code == 200
    assert "Prior nearby cells are hidden rather than displayed as current." in response.text
    assert "document.querySelectorAll('.cell').forEach(e=>e.remove())" in response.text
    assert "Nearby activity is hidden rather than showing stale or false precision." in response.text
    assert "window.location.assign('/account?next=/map')" in response.text


def test_browser_navigation_connects_radio_map_audience_and_operations() -> None:
    with client() as test_client:
        radio = test_client.get("/")
        map_page = test_client.get("/map")
        audience = test_client.get("/audience")
        operations = test_client.get("/ops")

    assert 'href="/map">Map</a>' in radio.text
    for target in (
        'href="/">Web Radio</a>',
        'href="/audience">Audience</a>',
        'href="/ops">Operations</a>',
    ):
        assert target in map_page.text
    assert 'href="/map">Map</a>' in audience.text
    assert 'href="/map">Map Awareness</a>' in operations.text
