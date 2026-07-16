import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Literal, cast
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import location as location_api
from app.api.auth import current_session
from app.auth.service import AuthenticatedSession
from app.config import Settings
from app.db.models import Account, Device, Session
from app.db.session import get_session
from app.location.consent import LocationConsentError, LocationConsentReceipt
from app.location.quality import LocationPolicyError
from app.location.service import LocationReceipt
from app.main import create_app


def settings(*, mutation_limit: int = 30) -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
        location_mutation_limit=mutation_limit,
    )


def identity() -> AuthenticatedSession:
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="ios",
        installation_id="location-route-synthetic",
    )
    session = Session(
        id=uuid.uuid4(),
        account=account,
        device=device,
        refresh_token_hash="synthetic-hash",
        expires_at=datetime(2026, 8, 1),
    )
    return AuthenticatedSession(account=account, device=device, session=session)


def authenticated_application(*, mutation_limit: int = 30) -> tuple[FastAPI, AsyncSession]:
    application = create_app(settings(mutation_limit=mutation_limit))
    current = identity()
    db = cast(AsyncSession, MagicMock())

    async def override_current() -> AuthenticatedSession:
        return current

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield db

    application.dependency_overrides[current_session] = override_current
    application.dependency_overrides[get_session] = override_db
    return application, db


def consent_payload() -> dict[str, object]:
    return {
        "policy_version": "location-v1",
        "disclosure_version": "location-disclosure-v1",
    }


def location_payload() -> dict[str, object]:
    return {
        "observed_at": "2026-07-15T12:00:00Z",
        "latitude": 40.0,
        "longitude": -75.0,
        "horizontal_accuracy_m": 10.0,
        "heading_deg": 90.0,
        "speed_mps": 5.0,
        "client_sequence": 1,
        "consent_policy_version": "location-v1",
    }


def test_location_routes_are_authenticated_owner_scoped_and_exact() -> None:
    schema = create_app(settings()).openapi()

    assert set(schema["paths"]["/api/v1/me/location-consent"]) == {"put", "delete"}
    assert set(schema["paths"]["/api/v1/me/location"]) == {"put", "delete"}
    for path in ("/api/v1/me/location-consent", "/api/v1/me/location"):
        for operation in schema["paths"][path].values():
            assert operation["security"] == [{"HTTPBearer": []}]
            assert operation["tags"] == ["location"]

    components = schema["components"]["schemas"]
    assert set(components["LocationConsentRequest"]["properties"]) == {
        "policy_version",
        "disclosure_version",
    }
    assert set(components["LocationConsentResponse"]["properties"]) == {
        "decision",
        "policy_version",
        "disclosure_version",
        "decided_at",
    }
    assert set(components["CurrentLocationRequest"]["properties"]) == set(location_payload())
    assert set(components["CurrentLocationResponse"]["properties"]) == {
        "accepted_sequence",
        "quality_state",
        "expires_at",
        "policy_version",
        "version",
    }
    assert set(components["CurrentLocationPauseResponse"]["properties"]) == {"state"}
    assert "requestBody" not in schema["paths"]["/api/v1/me/location-consent"]["delete"]


def test_location_routes_require_bearer_authentication_without_database_access() -> None:
    application = create_app(settings())
    with TestClient(application, raise_server_exceptions=False) as client:
        responses = [
            client.put("/api/v1/me/location-consent", json=consent_payload()),
            client.delete("/api/v1/me/location-consent"),
            client.put("/api/v1/me/location", json=location_payload()),
            client.delete("/api/v1/me/location"),
        ]

    assert {response.status_code for response in responses} == {401}
    assert {response.json()["code"] for response in responses} == {"AUTHENTICATION_REQUIRED"}
    assert {response.headers["WWW-Authenticate"] for response in responses} == {"Bearer"}


def test_location_contracts_return_metadata_without_private_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=UTC)

    async def consent(*args: object, **kwargs: object) -> LocationConsentReceipt:
        return LocationConsentReceipt(
            decision=cast(Literal["granted", "revoked"], kwargs["decision"]),
            policy_version="location-v1",
            disclosure_version="location-disclosure-v1",
            decided_at=now,
        )

    async def record(*args: object, **kwargs: object) -> LocationReceipt:
        return LocationReceipt(
            accepted_sequence=1,
            quality_state="usable",
            expires_at=now + timedelta(seconds=120),
            policy_version="location-v1",
            version=1,
        )

    async def remove(*args: object, **kwargs: object) -> bool:
        return True

    monkeypatch.setattr(location_api, "set_foreground_location_consent", consent)
    monkeypatch.setattr(location_api, "record_current_location", record)
    monkeypatch.setattr(location_api, "delete_current_location", remove)
    application, _ = authenticated_application()

    with TestClient(application) as client:
        granted = client.put("/api/v1/me/location-consent", json=consent_payload())
        revoked = client.delete("/api/v1/me/location-consent")
        recorded = client.put("/api/v1/me/location", json=location_payload())
        paused = client.delete("/api/v1/me/location")

    assert granted.status_code == 200
    assert granted.json()["decision"] == "granted"
    assert revoked.status_code == 200
    assert revoked.json()["decision"] == "revoked"
    assert recorded.status_code == 200
    assert recorded.json()["accepted_sequence"] == 1
    assert paused.json() == {"state": "paused"}
    combined = granted.text + revoked.text + recorded.text + paused.text
    for private_value in ("40.0", "-75.0", "90.0", "5.0", "location-route-synthetic"):
        assert private_value not in combined


def test_location_overposting_and_rate_limit_fail_without_echoing_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def remove(*args: object, **kwargs: object) -> bool:
        return False

    monkeypatch.setattr(location_api, "delete_current_location", remove)
    application, _ = authenticated_application(mutation_limit=1)
    payload = location_payload() | {"account_id": "private-account-selector"}

    with TestClient(application) as client:
        overposted = client.put("/api/v1/me/location", json=payload)
        first = client.delete("/api/v1/me/location")
        limited = client.delete("/api/v1/me/location")

    assert overposted.status_code == 422
    assert overposted.json()["code"] == "VALIDATION_ERROR"
    assert "private-account-selector" not in overposted.text
    assert first.status_code == 200
    assert limited.status_code == 429
    assert limited.json()["code"] == "LOCATION_RATE_LIMITED"
    assert int(limited.headers["Retry-After"]) >= 1


@pytest.mark.parametrize(
    ("code", "expected_status"),
    [
        ("LOCATION_SAMPLE_OUT_OF_ORDER", 409),
        ("LOCATION_CONSENT_REQUIRED", 409),
        ("LOCATION_MOVEMENT_IMPLAUSIBLE", 422),
        ("LOCATION_ACCURACY_UNUSABLE", 422),
    ],
)
def test_location_policy_failures_map_to_stable_non_disclosing_problems(
    monkeypatch: pytest.MonkeyPatch,
    code: str,
    expected_status: int,
) -> None:
    async def reject(*args: object, **kwargs: object) -> LocationReceipt:
        raise LocationPolicyError(code, "The location sample could not be accepted.")

    monkeypatch.setattr(location_api, "record_current_location", reject)
    application, _ = authenticated_application()

    with TestClient(application) as client:
        response = client.put("/api/v1/me/location", json=location_payload())

    assert response.status_code == expected_status
    assert response.json()["code"] == code
    assert response.json()["detail"] == "The location sample could not be accepted."
    for private_value in ("40.0", "-75.0", "90.0", "5.0"):
        assert private_value not in response.text


def test_stale_consent_grant_returns_conflict_but_withdrawal_needs_no_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def consent(*args: object, **kwargs: object) -> LocationConsentReceipt:
        if kwargs["decision"] == "granted":
            raise LocationConsentError(
                "LOCATION_POLICY_MISMATCH",
                "The foreground-location policy must be accepted again.",
            )
        return LocationConsentReceipt(
            decision="revoked",
            policy_version="old-policy",
            disclosure_version="old-disclosure",
            decided_at=datetime(2026, 7, 15, 12, tzinfo=UTC),
        )

    monkeypatch.setattr(location_api, "set_foreground_location_consent", consent)
    application, _ = authenticated_application()

    with TestClient(application) as client:
        stale = client.put("/api/v1/me/location-consent", json=consent_payload())
        withdrawn = client.delete("/api/v1/me/location-consent")

    assert stale.status_code == 409
    assert stale.json()["code"] == "LOCATION_POLICY_MISMATCH"
    assert withdrawn.status_code == 200
    assert withdrawn.json()["decision"] == "revoked"
