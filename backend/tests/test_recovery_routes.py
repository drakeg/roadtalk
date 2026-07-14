from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def settings() -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
        recovery_attempt_limit=3,
        recovery_attempt_window_seconds=120,
        recovery_mutation_limit=2,
        recovery_mutation_window_seconds=300,
    )


def test_recovery_routes_have_intended_authentication_boundaries() -> None:
    application = create_app(settings())
    with TestClient(application) as client:
        schema = client.get("/openapi.json").json()

    create_operation = schema["paths"]["/api/v1/me/recovery-key"]["post"]
    recover_operation = schema["paths"]["/api/v1/sessions/recover"]["post"]
    assert create_operation["security"] == [{"HTTPBearer": []}]
    assert "security" not in recover_operation
    request_properties = schema["components"]["schemas"]["RecoverySessionRequest"][
        "properties"
    ]
    assert set(request_properties) == {
        "recovery_key",
        "installation_id",
        "platform",
    }


def test_recovery_key_creation_requires_auth_without_database_access() -> None:
    application = create_app(settings())
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/me/recovery-key")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_recovery_limits_are_configured_without_managed_cache() -> None:
    application = create_app(settings())

    assert application.state.recovery_limiter.attempt_limit == 3
    assert application.state.recovery_limiter.attempt_window_seconds == 120
    assert application.state.recovery_limiter.mutation_limit == 2
    assert application.state.recovery_limiter.mutation_window_seconds == 300
