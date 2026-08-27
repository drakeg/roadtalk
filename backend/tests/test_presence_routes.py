import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import presence as presence_api
from app.api.auth import current_session
from app.auth.service import AuthenticatedSession
from app.config import Settings
from app.db.models import Account, Device, Session
from app.db.session import get_session
from app.main import create_app
from app.presence.lifecycle import PresenceSnapshot
from app.presence.policy import PresenceCell


def _settings() -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
    )


def _identity() -> AuthenticatedSession:
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="ios",
        installation_id="presence-route-synthetic",
    )
    session = Session(
        id=uuid.uuid4(),
        account=account,
        device=device,
        refresh_token_hash="presence-synthetic-hash",
        expires_at=datetime(2026, 9, 1, tzinfo=UTC),
    )
    return AuthenticatedSession(account=account, device=device, session=session)


def _application() -> tuple[FastAPI, AsyncSession]:
    application = create_app(_settings())
    current = _identity()
    db = cast(AsyncSession, MagicMock())

    async def override_current() -> AuthenticatedSession:
        return current

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield db

    application.dependency_overrides[current_session] = override_current
    application.dependency_overrides[get_session] = override_db
    return application, db


def test_presence_route_is_authenticated_get_only_with_no_selectors() -> None:
    schema = create_app(_settings()).openapi()
    operation = schema["paths"]["/api/v1/presence/nearby"]["get"]

    assert set(schema["paths"]["/api/v1/presence/nearby"]) == {"get"}
    assert operation["security"] == [{"HTTPBearer": []}]
    assert operation["tags"] == ["presence"]
    assert "parameters" not in operation
    assert "requestBody" not in operation


def test_presence_route_requires_authentication_without_database_access() -> None:
    application = create_app(_settings())
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/presence/nearby")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_presence_route_returns_only_coarse_cells(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2026, 8, 27, 12, tzinfo=UTC)

    async def snapshot(*args: object, **kwargs: object) -> PresenceSnapshot:
        return PresenceSnapshot(
            expires_at=now + timedelta(seconds=45),
            cells=(
                PresenceCell(
                    approximate_latitude=40.01,
                    approximate_longitude=-75.01,
                    density="few",
                    account_count=3,
                ),
            ),
        )

    monkeypatch.setattr(presence_api, "current_presence_snapshot", snapshot)
    application, _ = _application()
    with TestClient(application) as client:
        response = client.get("/api/v1/presence/nearby")

    assert response.status_code == 200
    assert response.json() == {
        "availability": "available",
        "policy_version": "presence-v1",
        "privacy_min_accounts": 3,
        "freshness": "fresh",
        "expires_at": "2026-08-27T12:00:45Z",
        "cells": [
            {
                "approximate_latitude": 40.01,
                "approximate_longitude": -75.01,
                "cell_size_m": 2000,
                "density": "few",
            }
        ],
    }
    encoded = response.text.lower()
    for forbidden in (
        "account_id",
        "device_id",
        "callsign",
        "distance",
        "bearing",
        "heading",
        "speed",
        "route",
        "corridor",
        "destination",
        "history",
    ):
        assert forbidden not in encoded


def test_presence_route_rejects_every_selector_before_querying(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    async def snapshot(*args: object, **kwargs: object) -> PresenceSnapshot:
        nonlocal called
        called = True
        raise AssertionError("selector must fail before presence query")

    monkeypatch.setattr(presence_api, "current_presence_snapshot", snapshot)
    application, _ = _application()
    with TestClient(application) as client:
        response = client.get("/api/v1/presence/nearby?radius=5000")

    assert response.status_code == 422
    assert response.json()["code"] == "PRESENCE_SELECTOR_FORBIDDEN"
    assert called is False
