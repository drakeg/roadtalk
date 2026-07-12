from typing import Any

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "environment": "test",
        "docs_enabled": False,
        "log_level": "CRITICAL",
        "database_check_enabled": False,
    }
    values.update(overrides)
    return Settings(**values)


def client() -> TestClient:
    return TestClient(
        create_app(test_settings(version="test-version")),
        raise_server_exceptions=False,
    )


def test_liveness_returns_request_id() -> None:
    with client() as test_client:
        response = test_client.get("/health/live", headers={"X-Request-ID": "test-request"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "test-request"


def test_oversized_request_id_is_replaced() -> None:
    with client() as test_client:
        response = test_client.get("/health/live", headers={"X-Request-ID": "x" * 200})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "x" * 200
    assert len(response.headers["X-Request-ID"]) == 36


def test_readiness_is_ready_without_registered_dependencies() -> None:
    with client() as test_client:
        response = test_client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {}}


def test_database_readiness_is_registered_by_default() -> None:
    application = create_app(test_settings(database_check_enabled=True))
    assert [check.name for check in application.state.readiness._checks] == ["database"]


def test_version_endpoint_is_versioned() -> None:
    with client() as test_client:
        response = test_client.get("/api/v1/system/version")
    assert response.status_code == 200
    assert response.json() == {
        "name": "RoadTalk API",
        "version": "test-version",
        "environment": "test",
    }


def test_docs_are_disabled_by_configuration() -> None:
    with client() as test_client:
        response = test_client.get("/openapi.json")
    assert response.status_code == 404
    body = response.json()
    assert body["status"] == 404
    assert body["request_id"]


def test_unhandled_errors_are_sanitized() -> None:
    application = create_app(test_settings())

    @application.get("/explode")
    async def explode() -> None:
        raise RuntimeError("sensitive internal detail")

    with TestClient(application, raise_server_exceptions=False) as test_client:
        response = test_client.get("/explode")
    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "sensitive internal detail" not in response.text
    assert body["request_id"] == response.headers["X-Request-ID"]
