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


def test_browser_audience_mode_is_accessible_and_privacy_minimized() -> None:
    with client() as test_client:
        response = test_client.get("/audience")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "RoadTalk | Audience Mode" in response.text
    assert "Nearby or Same road" in response.text
    assert 'aria-label="Audience mode"' in response.text
    assert 'aria-pressed="false"' in response.text
    assert "/api/v1/me/route-mode" in response.text
    assert "Back to Web Radio" in response.text
    assert "fails closed" in response.text
    assert "who matched" in response.text
    assert "crypto.randomUUID()" in response.text


def test_browser_audience_mode_rejects_disclosing_api_fields_before_rendering() -> None:
    with client() as test_client:
        response = test_client.get("/audience")

    assert response.status_code == 200
    for field in (
        "road_name",
        "provider_corridor_ref",
        "corridor_digest",
        "direction",
        "latitude",
        "longitude",
        "distance_m",
        "bearing",
        "account_id",
        "device_id",
        "participant_ref",
        "eligibility_reason",
    ):
        assert repr(field) in response.text or f"'{field}'" in response.text
    assert "invalid response" in response.text
