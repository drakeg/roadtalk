from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def application_settings() -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
    )


def test_callsign_availability_route_is_versioned_and_authenticated() -> None:
    application = create_app(application_settings())
    with TestClient(application) as client:
        schema = client.get("/openapi.json").json()

    operation = schema["paths"]["/api/v1/callsigns/availability"]["get"]
    assert operation["tags"] == ["identity"]
    assert operation["security"] == [{"HTTPBearer": []}]


def test_callsign_availability_requires_bearer_token_without_database_access() -> None:
    application = create_app(application_settings())
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get(
            "/api/v1/callsigns/availability",
            params={"callsign": "Road-Runner"},
        )

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_callsign_limits_are_configurable() -> None:
    settings = Settings(
        environment="test",
        callsign_availability_limit=5,
        callsign_availability_window_seconds=120,
    )
    application = create_app(settings)

    assert application.state.callsign_limiter.limit == 5
    assert application.state.callsign_limiter.window_seconds == 120
