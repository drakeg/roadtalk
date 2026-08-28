from fastapi.testclient import TestClient

from app.auth.passwords import hash_password, normalize_username, verify_password
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


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)


def test_username_normalization_is_private_login_identifier() -> None:
    assert normalize_username("  Road.Driver_1 ") == "road.driver_1"


def test_account_page_explains_persistent_callsign_and_auth_actions() -> None:
    with client() as test_client:
        response = test_client.get("/account")

    assert response.status_code == 200
    html = response.text
    assert "Your private username and password identify your account" in html
    assert "Your public call sign belongs to that account profile" in html
    assert "Log in" in html
    assert "Create / protect this account" in html
    assert "/api/v1/auth/login" in html
    assert "/api/v1/auth/register" in html
    assert "/api/v1/auth/promote" in html
    assert "account_type==='anonymous'" in html


def test_radio_routes_unsigned_browser_to_account_page_first() -> None:
    with client() as test_client:
        response = test_client.get("/")

    assert response.status_code == 200
    assert "location.replace('/account')" in response.text
    assert 'href="/account">Account</a>' in response.text
