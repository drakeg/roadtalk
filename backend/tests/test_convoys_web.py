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


def test_convoy_browser_is_accessible_and_privacy_bounded() -> None:
    with client() as test_client:
        response = test_client.get("/convoys")

    assert response.status_code == 200
    assert "RoadTalk | Convoys" in response.text
    assert 'role="status" aria-live="polite"' in response.text
    assert ":focus-visible" in response.text
    assert "Travel together without location history" in response.text
    assert "Membership never grants communication access" in response.text
    assert "coordinates, routes, or movement history" in response.text


def test_convoy_browser_has_lifecycle_controls_and_destructive_confirmations() -> None:
    with client() as test_client:
        response = test_client.get("/convoys")

    assert response.status_code == 200
    for endpoint in (
        "/api/v1/convoys/me",
        "/api/v1/convoys/join",
        "/api/v1/convoys/leave",
        "/api/v1/convoys/disband",
        "/api/v1/convoys/awareness",
    ):
        assert endpoint in response.text
    assert "Leave this convoy?" in response.text
    assert "Disband this convoy for every member?" in response.text
    assert "confirm(" in response.text


def test_convoy_api_requires_authentication() -> None:
    with client() as test_client:
        unauthenticated = (
            test_client.get("/api/v1/convoys/me"),
            test_client.post("/api/v1/convoys", json={"display_name": "Road crew"}),
            test_client.post("/api/v1/convoys/join", json={"convoy_id": "00000000-0000-0000-0000-000000000001"}),
            test_client.post("/api/v1/convoys/leave"),
            test_client.post("/api/v1/convoys/disband"),
            test_client.get("/api/v1/convoys/awareness"),
        )

    assert {response.status_code for response in unauthenticated} == {401}


def test_convoy_api_contract_is_closed_and_non_disclosing() -> None:
    schema = create_app(
        Settings(
            environment="test",
            docs_enabled=True,
            log_level="CRITICAL",
            database_check_enabled=False,
        )
    ).openapi()
    components = schema["components"]["schemas"]
    assert components["CreateConvoyRequest"]["additionalProperties"] is False
    assert components["JoinConvoyRequest"]["additionalProperties"] is False
    response_fields = set(components["ConvoyStatusResponse"]["properties"])
    assert response_fields == {"convoy_id", "membership_id", "display_name", "role", "state"}
    encoded = str(components["ConvoyStatusResponse"]).lower()
    for forbidden in ("latitude", "longitude", "route_history", "provider_token", "password"):
        assert forbidden not in encoded


def test_convoy_api_openapi_rejects_overposting() -> None:
    schema = create_app(
        Settings(
            environment="test",
            docs_enabled=True,
            log_level="CRITICAL",
            database_check_enabled=False,
        )
    ).openapi()
    components = schema["components"]["schemas"]
    assert components["CreateConvoyRequest"]["additionalProperties"] is False
    assert components["JoinConvoyRequest"]["additionalProperties"] is False
