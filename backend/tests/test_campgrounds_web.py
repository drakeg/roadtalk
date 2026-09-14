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


def test_campground_browser_is_accessible_and_explicitly_deterministic() -> None:
    with client() as test_client:
        response = test_client.get("/campgrounds")

    assert response.status_code == 200
    assert "RoadTalk | Campgrounds" in response.text
    assert 'aria-label="Campground filters"' in response.text
    assert 'role="status" aria-live="polite"' in response.text
    assert ":focus-visible" in response.text
    assert "Deterministic test catalog only" in response.text
    assert "not a live or complete directory" in response.text
    assert "/api/v1/campgrounds/catalog" in response.text


def test_campground_browser_has_search_filters_and_no_commerce_or_occupancy_actions() -> None:
    with client() as test_client:
        response = test_client.get("/campgrounds")

    assert response.status_code == 200
    assert 'id="q" type="search"' in response.text
    assert 'id="cat"' in response.text
    assert 'id="amenity"' in response.text
    assert "Browsing or selecting a campground never grants communication access" in response.text
    lowered = response.text.lower()
    assert "no reservations, booking, payments, campsite occupancy, or member lists" in lowered
    assert "background location" not in lowered
    assert "background tracking" not in lowered


def test_public_catalog_is_bounded_and_marks_provenance() -> None:
    with client() as test_client:
        response = test_client.get("/api/v1/campgrounds/catalog")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "deterministic_local"
    assert body["freshness"] == "deterministic"
    assert body["live_directory"] is False
    assert 1 <= len(body["campgrounds"]) <= 100
    encoded = str(body).lower()
    for forbidden in ("occupancy_count", "member_ids", "campsite_id", "arrival_at", "departure_at"):
        assert forbidden not in encoded


def test_current_context_requires_existing_session_and_accepts_no_selector() -> None:
    with client() as test_client:
        unauthenticated = test_client.get("/api/v1/campgrounds/context")
        selected = test_client.get("/api/v1/campgrounds/context?campground_id=cg_finger_lakes_001")

    assert unauthenticated.status_code == 401
    assert selected.status_code == 401
