import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import route_mode as route_mode_api
from app.api.auth import current_session
from app.auth.service import AuthenticatedSession
from app.config import Settings
from app.db.models import Account, Device, Session
from app.db.session import get_session
from app.main import create_app
from app.route_mode.service import RouteModeError, RouteModeReceipt


def settings() -> Settings:
    return Settings(
        environment="test", docs_enabled=True, log_level="CRITICAL", database_check_enabled=False
    )


def authenticated_application() -> FastAPI:
    application = create_app(settings())
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(), account=account, platform="ios", installation_id="route-mode-synthetic"
    )
    session = Session(
        id=uuid.uuid4(),
        account=account,
        device=device,
        refresh_token_hash="synthetic-hash",
        expires_at=datetime(2026, 9, 1),
    )
    current = AuthenticatedSession(account=account, device=device, session=session)
    db = cast(AsyncSession, MagicMock())

    async def override_current() -> AuthenticatedSession:
        return current

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield db

    application.dependency_overrides[current_session] = override_current
    application.dependency_overrides[get_session] = override_db
    return application


def receipt(mode: str = "nearby", version: int = 1) -> RouteModeReceipt:
    return RouteModeReceipt(
        mode,
        version,
        datetime(2026, 8, 22, 12, tzinfo=UTC),
        "available" if mode == "nearby" else "unavailable",
    )


def test_route_mode_openapi_is_exact_authenticated_and_non_disclosing() -> None:
    schema = create_app(settings()).openapi()
    read = schema["paths"]["/api/v1/me/route-mode"]["get"]
    update = schema["paths"]["/api/v1/me/route-mode"]["put"]
    assert read["security"] == [{"HTTPBearer": []}]
    assert update["security"] == [{"HTTPBearer": []}]
    assert read["tags"] == update["tags"] == ["route-mode"]
    components = schema["components"]["schemas"]
    assert set(components["RouteModeResponse"]["properties"]) == {
        "mode",
        "version",
        "selected_at",
        "availability",
    }
    assert set(components["RouteModeUpdateRequest"]["properties"]) == {"mode", "expected_version"}
    serialized = str(components).lower()
    for forbidden in (
        "route_name",
        "road",
        "corridor",
        "provider",
        "direction",
        "coordinate",
        "audience",
    ):
        assert forbidden not in serialized


def test_route_mode_routes_require_authentication() -> None:
    with TestClient(create_app(settings()), raise_server_exceptions=False) as client:
        responses = (
            client.get("/api/v1/me/route-mode"),
            client.put("/api/v1/me/route-mode", json={"mode": "nearby", "expected_version": 1}),
        )
    assert {response.status_code for response in responses} == {401}


def test_route_mode_read_and_update_return_semantic_state(monkeypatch: pytest.MonkeyPatch) -> None:
    async def read(*args: object, **kwargs: object) -> RouteModeReceipt:
        return receipt()

    async def update(*args: object, **kwargs: object) -> RouteModeReceipt:
        return receipt("same_road", 2)

    monkeypatch.setattr(route_mode_api, "get_route_mode", read)
    monkeypatch.setattr(route_mode_api, "set_route_mode", update)
    with TestClient(authenticated_application()) as client:
        current = client.get("/api/v1/me/route-mode")
        changed = client.put(
            "/api/v1/me/route-mode", json={"mode": "same_road", "expected_version": 1}
        )
    assert current.json()["mode"] == "nearby"
    assert changed.json() == {
        "mode": "same_road",
        "version": 2,
        "selected_at": "2026-08-22T12:00:00Z",
        "availability": "unavailable",
    }


def test_route_mode_rejects_overposting_and_invalid_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    async def update(*args: object, **kwargs: object) -> RouteModeReceipt:
        return receipt()

    monkeypatch.setattr(route_mode_api, "set_route_mode", update)
    with TestClient(authenticated_application()) as client:
        extra = client.put(
            "/api/v1/me/route-mode",
            json={"mode": "nearby", "expected_version": 1, "road": "secret"},
        )
        invalid = client.put(
            "/api/v1/me/route-mode", json={"mode": "automatic", "expected_version": 1}
        )
    assert extra.status_code == invalid.status_code == 422


def test_route_mode_conflict_is_stable_and_non_disclosing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def reject(*args: object, **kwargs: object) -> RouteModeReceipt:
        raise RouteModeError(
            "ROUTE_MODE_VERSION_CONFLICT", "The route mode changed; reload it before retrying."
        )

    monkeypatch.setattr(route_mode_api, "set_route_mode", reject)
    with TestClient(authenticated_application()) as client:
        response = client.put(
            "/api/v1/me/route-mode", json={"mode": "same_road", "expected_version": 1}
        )
    assert response.status_code == 409
    assert response.json()["code"] == "ROUTE_MODE_VERSION_CONFLICT"
    for forbidden in ("road", "corridor", "provider", "direction", "location", "audience"):
        assert forbidden not in response.text.lower()
