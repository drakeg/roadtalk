from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_authentication_routes_are_versioned() -> None:
    application = create_app(
        Settings(
            environment="test",
            docs_enabled=True,
            log_level="CRITICAL",
            database_check_enabled=False,
        )
    )
    with TestClient(application) as client:
        schema = client.get("/openapi.json").json()

    assert {
        "/api/v1/auth/anonymous",
        "/api/v1/auth/refresh",
        "/api/v1/auth/session",
        "/api/v1/auth/logout",
        "/api/v1/auth/devices/{device_id}",
    } <= set(schema["paths"])


def test_protected_route_requires_bearer_token_without_touching_database() -> None:
    application = create_app(
        Settings(
            environment="test",
            docs_enabled=False,
            log_level="CRITICAL",
            database_check_enabled=False,
        )
    )
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/auth/session")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"
    assert response.headers["WWW-Authenticate"] == "Bearer"
