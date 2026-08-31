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


def test_registered_account_validation_identifies_password_requirement() -> None:
    with client() as test_client:
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "roaduser",
                "password": "short",
                "installation_id": "web-1234567890123456",
                "platform": "web",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["detail"] == "Password: String should have at least 12 characters."
    assert body["errors"][0]["location"] == ["body", "password"]


def test_registered_account_validation_identifies_username_requirement() -> None:
    with client() as test_client:
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "x",
                "password": "valid-password-value",
                "installation_id": "web-1234567890123456",
                "platform": "web",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Username: String should have at least 3 characters."
    assert body["errors"][0]["location"] == ["body", "username"]
