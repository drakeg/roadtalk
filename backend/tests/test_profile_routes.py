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


def test_profile_routes_are_owner_scoped_versioned_and_authenticated() -> None:
    application = create_app(application_settings())
    with TestClient(application) as client:
        schema = client.get("/openapi.json").json()

    profile_path = schema["paths"]["/api/v1/me/profile"]
    assert set(profile_path) == {"get", "patch"}
    assert profile_path["get"]["security"] == [{"HTTPBearer": []}]
    assert profile_path["patch"]["security"] == [{"HTTPBearer": []}]
    assert "account_id" not in profile_path["patch"].get("parameters", [])

    public_fields = schema["components"]["schemas"]["PublicIdentity"]["properties"]
    assert set(public_fields) == {"callsign", "avatar_id"}
    update_fields = schema["components"]["schemas"]["ProfileUpdateRequest"]["properties"]
    assert set(update_fields) == {"version", "callsign"}


def test_profile_routes_require_bearer_token_without_database_access() -> None:
    application = create_app(application_settings())
    with TestClient(application, raise_server_exceptions=False) as client:
        read_response = client.get("/api/v1/me/profile")
        update_response = client.patch(
            "/api/v1/me/profile",
            json={"version": 0, "callsign": "Road-Runner"},
        )

    assert read_response.status_code == 401
    assert update_response.status_code == 401
    assert read_response.json()["code"] == "AUTHENTICATION_REQUIRED"
    assert update_response.json()["code"] == "AUTHENTICATION_REQUIRED"
