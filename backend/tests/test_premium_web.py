import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_session
from app.auth.service import AuthenticatedSession
from app.config import Settings
from app.db.models import Account, Device, Session
from app.db.session import get_session
from app.main import create_app
from app.premium.provider import FakePremiumProvider, PremiumProviderBoundary


def _settings(**overrides: object) -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
        **overrides,  # type: ignore[arg-type]
    )


def _identity() -> AuthenticatedSession:
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="web",
        installation_id="premium-route-synthetic",
    )
    session = Session(
        id=uuid.uuid4(),
        account=account,
        device=device,
        refresh_token_hash="premium-synthetic-hash",
        expires_at=datetime(2026, 12, 1, tzinfo=UTC),
    )
    return AuthenticatedSession(account=account, device=device, session=session)


def _authenticated(application: FastAPI) -> AuthenticatedSession:
    current = _identity()

    async def override_current() -> AuthenticatedSession:
        return current

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield cast(AsyncSession, MagicMock())

    application.dependency_overrides[current_session] = override_current
    application.dependency_overrides[get_session] = override_db
    return current


def test_premium_page_is_accessible_and_states_baseline_preservation() -> None:
    with TestClient(create_app(_settings())) as client:
        response = client.get("/premium")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    html = response.text
    for token in (
        "RoadTalk | Premium",
        'role="status" aria-live="polite"',
        ":focus-visible",
        'aria-labelledby="entitlement-heading"',
        '<button id="check" type="button">Check Premium status</button>',
        "Premium never changes who you can hear or talk to.",
        "stay available without Premium",
    ):
        assert token in html


def test_premium_page_offers_no_checkout_or_payment_collection() -> None:
    with TestClient(create_app(_settings())) as client:
        html = client.get("/premium").text

    assert "Premium purchase is not available." in html
    assert "<form" not in html
    assert "<input" not in html
    lowered = html.lower()
    for forbidden in (
        "stripe",
        "paypal",
        "apple pay",
        "google pay",
        "card number",
        "cvv",
        "billing address",
        "/checkout",
        "/purchase",
        "latitude",
        "longitude",
    ):
        assert forbidden not in lowered


def test_premium_page_clears_offline_and_stale_status_and_never_trusts_client_state() -> None:
    with TestClient(create_app(_settings())) as client:
        html = client.get("/premium").text

    assert "/api/v1/me/premium" in html
    assert "window.addEventListener('offline'" in html
    assert "navigator.onLine" in html
    assert "s.valid_until" in html
    assert "setTimeout(()=>clearStatus(" in html
    assert "setInterval" not in html
    assert "innerHTML" not in html
    # Premium state is only rendered from the server response, never persisted locally.
    assert "localStorage.setItem('rt_premium" not in html
    assert "sessionStorage" not in html


def test_dashboard_links_to_premium() -> None:
    with TestClient(create_app(_settings())) as client:
        assert 'href="/premium"' in client.get("/").text


def test_premium_status_requires_authentication() -> None:
    with TestClient(create_app(_settings()), raise_server_exceptions=False) as client:
        response = client.get("/api/v1/me/premium")

    assert response.status_code == 401


def test_premium_status_defaults_to_disabled_provider() -> None:
    application = create_app(_settings())
    _authenticated(application)
    with TestClient(application) as client:
        response = client.get("/api/v1/me/premium")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["availability"] == "provider_disabled"
    assert body["tier"] == "free"
    assert body["premium_experience_allowed"] is False
    assert body["checkout_available"] is False


def test_premium_status_reads_only_the_callers_account() -> None:
    application = create_app(_settings(premium_provider="fake"))
    current = _authenticated(application)
    other = uuid.uuid4()
    provider = FakePremiumProvider(states={current.account.id: "active", other: "revoked"})
    application.state.premium_provider = PremiumProviderBoundary(provider)

    with TestClient(application) as client:
        response = client.get("/api/v1/me/premium", params={"account_id": str(other)})

    assert response.status_code == 200
    assert response.json()["tier"] == "premium"
    assert [request.account_id for request in provider.requests] == [current.account.id]


def test_premium_status_is_read_only() -> None:
    application = create_app(_settings())
    _authenticated(application)
    with TestClient(application) as client:
        for method in ("post", "put", "patch", "delete"):
            response = getattr(client, method)("/api/v1/me/premium")
            assert response.status_code == 405


def test_premium_status_contract_is_closed() -> None:
    schema = create_app(_settings()).openapi()
    component = schema["components"]["schemas"]["PremiumStatus"]
    assert component["additionalProperties"] is False
    assert "/api/v1/me/premium" in schema["paths"]
    assert set(schema["paths"]["/api/v1/me/premium"]) == {"get"}


def test_fake_premium_provider_is_rejected_outside_local_and_test() -> None:
    for environment in ("field-test", "production"):
        with pytest.raises(ValidationError, match="premium provider must remain disabled"):
            Settings(environment=environment, premium_provider="fake")
