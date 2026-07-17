from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import recovery as recovery_api
from app.config import Settings
from app.main import create_app
from app.recovery.service import RecoveryError


def settings(*, recovery_attempt_limit: int = 10) -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
        recovery_attempt_limit=recovery_attempt_limit,
    )


def test_openapi_exposes_only_approved_through_s03_d08_contracts() -> None:
    schema = create_app(settings()).openapi()

    assert set(schema["paths"]) == {
        "/api/v1/auth/anonymous",
        "/api/v1/auth/devices/{device_id}",
        "/api/v1/auth/logout",
        "/api/v1/auth/refresh",
        "/api/v1/auth/session",
        "/api/v1/avatars",
        "/api/v1/callsigns/availability",
        "/api/v1/me/profile",
        "/api/v1/me/recovery-key",
        "/api/v1/me/location",
        "/api/v1/me/location-consent",
        "/api/v1/nearby/summary",
        "/api/v1/sessions/recover",
        "/api/v1/system/version",
    }
    components = schema["components"]["schemas"]
    assert set(components["PublicIdentity"]["properties"]) == {"callsign", "avatar_id"}
    assert set(components["ProfileResponse"]["properties"]) == {
        "identity",
        "setup_completed",
        "version",
    }
    assert set(components["ProfileUpdateRequest"]["properties"]) == {
        "version",
        "callsign",
        "avatar_id",
    }
    recovery_request = components["RecoverySessionRequest"]["properties"]
    assert set(recovery_request) == {"recovery_key", "installation_id", "platform"}
    assert recovery_request["recovery_key"]["format"] == "password"
    assert recovery_request["recovery_key"]["writeOnly"] is True
    assert set(components["RecoveryKeyResponse"]["properties"]) == {
        "recovery_key",
        "key_version",
    }
    assert set(components["RecoverySessionResponse"]["properties"]) == {
        "access_token",
        "refresh_token",
        "token_type",
        "expires_in",
        "account_id",
        "device_id",
        "session_id",
        "recovery_key",
        "recovery_key_version",
    }

    public_surface = set(schema["paths"])
    for name, component in components.items():
        if name in {"HTTPValidationError", "ValidationError"}:
            continue
        public_surface.add(name)
        public_surface.update(component.get("properties", {}))
    encoded = " ".join(sorted(public_surface)).lower()
    for forbidden in (
        "biography",
        "email",
        "background_location",
        "microphone",
        "notification",
        "phone_number",
        "social_link",
        "uploaded_avatar",
        "vehicle",
    ):
        assert forbidden not in encoded


@pytest.mark.parametrize("candidate", ["malformed", "unknown", "replayed"])
def test_recovery_http_failures_are_non_enumerating(
    monkeypatch: pytest.MonkeyPatch,
    candidate: str,
) -> None:
    attempted_key = f"rtk1.{candidate}.synthetic-secret"

    async def fail_recovery(*args: Any, **kwargs: Any) -> None:
        raise RecoveryError(
            "RECOVERY_FAILED",
            "The account could not be recovered with that key.",
        )

    monkeypatch.setattr(recovery_api, "recover_account", fail_recovery)
    application = create_app(settings())
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/sessions/recover",
            json={
                "recovery_key": attempted_key,
                "installation_id": f"installation-{candidate}-123456",
                "platform": "ios",
            },
        )

    assert response.status_code == 401
    assert response.json()["code"] == "RECOVERY_FAILED"
    assert response.json()["detail"] == "The account could not be recovered with that key."
    assert attempted_key not in response.text
    assert candidate not in response.text


def test_recovery_http_rate_limit_is_stable_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_recovery(*args: Any, **kwargs: Any) -> None:
        raise RecoveryError(
            "RECOVERY_FAILED",
            "The account could not be recovered with that key.",
        )

    monkeypatch.setattr(recovery_api, "recover_account", fail_recovery)
    application = create_app(settings(recovery_attempt_limit=1))
    payload = {
        "recovery_key": "synthetic-candidate",
        "installation_id": "installation-rate-limit-123456",
        "platform": "android",
    }
    with TestClient(application) as client:
        first = client.post("/api/v1/sessions/recover", json=payload)
        limited = client.post("/api/v1/sessions/recover", json=payload)

    assert first.status_code == 401
    assert limited.status_code == 429
    assert limited.json()["code"] == "RECOVERY_RATE_LIMITED"
    assert limited.json()["detail"] == "Recovery requests are temporarily limited."
    assert int(limited.headers["Retry-After"]) >= 1
    assert payload["recovery_key"] not in limited.text
    assert payload["installation_id"] not in limited.text
