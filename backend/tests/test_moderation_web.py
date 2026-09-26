from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_browser_moderation_page_has_accessible_confirmation_and_safe_degraded_copy() -> None:
    client = TestClient(create_app(Settings(environment="test")))
    response = client.get("/safety")
    assert response.status_code == 200
    body = response.text
    assert 'role="status"' in body
    assert "confirm(" in body
    assert "Existing server-side restrictions remain enforced." in body
    assert "location, route, device, channel, convoy" in body
    assert "free_text" not in body
    assert "evidence" not in body


def test_browser_moderation_payloads_are_closed_and_bounded() -> None:
    client = TestClient(create_app(Settings(environment="test")))
    schema = client.get("/openapi.json").json()
    report = schema["components"]["schemas"]["ReportCommand"]
    restriction = schema["components"]["schemas"]["RestrictionCommand"]
    assert report["additionalProperties"] is False
    assert restriction["additionalProperties"] is False
    assert set(report["properties"]) == {"subject_account_id", "reason", "idempotency_key"}
    assert set(restriction["properties"]) == {"subject_account_id", "kind"}
