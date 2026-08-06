import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import ptt as ptt_api
from app.api.auth import current_session
from app.auth.service import AuthenticatedSession
from app.config import Settings
from app.db.models import Account, Device, Session
from app.db.session import get_session
from app.main import create_app
from app.ptt.service import (
    GrantError,
    GrantReleaseReceipt,
    PublicationReceipt,
    ReceiveGrantReceipt,
    TransmitGrantReceipt,
)

IDEMPOTENCY_KEY = "synthetic-key-0001"


def settings(*, receive_limit: int = 10) -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
        ptt_receive_grant_limit=receive_limit,
    )


def identity() -> AuthenticatedSession:
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="ios",
        installation_id="ptt-route-synthetic",
    )
    session = Session(
        id=uuid.uuid4(),
        account=account,
        device=device,
        refresh_token_hash="synthetic-hash",
        expires_at=datetime(2026, 8, 1),
    )
    return AuthenticatedSession(account=account, device=device, session=session)


def authenticated_application(*, receive_limit: int = 10) -> FastAPI:
    application = create_app(settings(receive_limit=receive_limit))
    current = identity()
    db = cast(AsyncSession, MagicMock())

    async def override_current() -> AuthenticatedSession:
        return current

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield db

    application.dependency_overrides[current_session] = override_current
    application.dependency_overrides[get_session] = override_db
    return application


def test_ptt_openapi_is_authenticated_and_server_controlled() -> None:
    schema = create_app(settings()).openapi()
    create = schema["paths"]["/api/v1/ptt/grants"]["post"]
    release = schema["paths"]["/api/v1/ptt/grants/{grant_id}"]["delete"]
    transmit = schema["paths"]["/api/v1/ptt/grants/{receive_grant_id}/transmit"]["post"]
    publication = schema["paths"]["/api/v1/ptt/grants/{transmit_grant_id}/publication"]["post"]

    assert create["security"] == [{"HTTPBearer": []}]
    assert release["security"] == [{"HTTPBearer": []}]
    assert transmit["security"] == [{"HTTPBearer": []}]
    assert publication["security"] == [{"HTTPBearer": []}]
    assert create["tags"] == ["push-to-talk"]
    assert release["tags"] == ["push-to-talk"]
    properties = schema["components"]["schemas"]["ReceiveGrantRequest"]["properties"]
    assert set(properties) == {"mode"}
    response_properties = schema["components"]["schemas"]["ReceiveGrantResponse"]["properties"]
    assert set(response_properties) == {
        "grant_id",
        "mode",
        "provider",
        "room_ref",
        "participant_ref",
        "allowed_actions",
        "allowed_track_sources",
        "issued_at",
        "expires_at",
        "policy_version",
        "replayed",
        "server_url",
        "participant_token",
    }
    transmit_properties = schema["components"]["schemas"]["TransmitGrantRequest"]["properties"]
    assert transmit_properties == {}
    transmit_response = schema["components"]["schemas"]["TransmitGrantResponse"]["properties"]
    assert set(transmit_response) == {
        "grant_id",
        "receive_grant_id",
        "mode",
        "allowed_actions",
        "allowed_track_sources",
        "issued_at",
        "expires_at",
        "policy_version",
        "replayed",
    }
    publication_properties = schema["components"]["schemas"]["PublicationRequest"]["properties"]
    assert set(publication_properties) == {"track_ref"}
    publication_response = schema["components"]["schemas"]["PublicationResponse"]["properties"]
    assert set(publication_response) == {
        "transmit_grant_id",
        "delivery_state",
        "proximity_policy_version",
        "evaluated_at",
        "expires_at",
        "replayed",
    }


def test_ptt_routes_require_authentication_and_idempotency_key() -> None:
    application = create_app(settings())
    authenticated = authenticated_application()
    grant_id = uuid.uuid4()
    with TestClient(application, raise_server_exceptions=False) as client:
        unauthenticated = client.post(
            "/api/v1/ptt/grants",
            json={"mode": "receive"},
            headers={"Idempotency-Key": IDEMPOTENCY_KEY},
        )
        release = client.delete(
            f"/api/v1/ptt/grants/{grant_id}",
            headers={"Idempotency-Key": IDEMPOTENCY_KEY},
        )
        publication = client.post(
            f"/api/v1/ptt/grants/{grant_id}/publication",
            json={"track_ref": "track_opaque"},
        )
    with TestClient(authenticated, raise_server_exceptions=False) as client:
        missing_key = client.post("/api/v1/ptt/grants", json={"mode": "receive"})

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["code"] == "AUTHENTICATION_REQUIRED"
    assert missing_key.status_code == 422
    assert release.status_code == 401
    assert publication.status_code == 401


def test_receive_creation_returns_token_once_and_release_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 24, 1, tzinfo=UTC)
    grant_id = uuid.uuid4()
    calls = 0

    async def create(*args: object, **kwargs: object) -> ReceiveGrantReceipt:
        nonlocal calls
        calls += 1
        return ReceiveGrantReceipt(
            grant_id=grant_id,
            room_ref="rm_opaque",
            participant_ref="pt_opaque",
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
            policy_version="ptt-v1",
            replayed=calls > 1,
            server_url=None if calls > 1 else "wss://synthetic.invalid",
            participant_token=None if calls > 1 else "synthetic-one-time-token",
        )

    async def release(*args: object, **kwargs: object) -> GrantReleaseReceipt:
        return GrantReleaseReceipt(
            grant_id=grant_id,
            released_at=now + timedelta(seconds=1),
            replayed=False,
        )

    monkeypatch.setattr(ptt_api, "create_receive_grant", create)
    monkeypatch.setattr(ptt_api, "release_owned_grant", release)
    application = authenticated_application()
    headers = {"Idempotency-Key": IDEMPOTENCY_KEY}

    with TestClient(application) as client:
        initial = client.post("/api/v1/ptt/grants", json={"mode": "receive"}, headers=headers)
        replay = client.post("/api/v1/ptt/grants", json={"mode": "receive"}, headers=headers)
        released = client.delete(f"/api/v1/ptt/grants/{grant_id}", headers=headers)

    assert initial.status_code == 201
    assert initial.json()["participant_token"] == "synthetic-one-time-token"
    assert replay.status_code == 200
    assert replay.json()["participant_token"] is None
    assert replay.json()["server_url"] is None
    assert released.json()["state"] == "released"
    combined = replay.text + released.text
    assert "synthetic-one-time-token" not in combined
    assert "ptt-route-synthetic" not in combined


def test_transmit_is_microphone_only_and_returns_no_provider_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 24, 1, tzinfo=UTC)
    receive_grant_id = uuid.uuid4()
    calls = 0

    async def create(*args: object, **kwargs: object) -> TransmitGrantReceipt:
        nonlocal calls
        calls += 1
        return TransmitGrantReceipt(
            grant_id=uuid.uuid4(),
            receive_grant_id=receive_grant_id,
            issued_at=now,
            expires_at=now + timedelta(seconds=30),
            policy_version="ptt-v1",
            replayed=calls > 1,
        )

    monkeypatch.setattr(ptt_api, "create_transmit_grant", create)
    application = authenticated_application()
    path = f"/api/v1/ptt/grants/{receive_grant_id}/transmit"
    headers = {"Idempotency-Key": IDEMPOTENCY_KEY}
    with TestClient(application) as client:
        initial = client.post(path, json={}, headers=headers)
        replay = client.post(path, json={}, headers=headers)
        overposted = client.post(
            path,
            json={"can_publish_data": True, "track_source": "camera"},
            headers={"Idempotency-Key": "synthetic-key-0002"},
        )

    assert initial.status_code == 201
    assert initial.json()["allowed_track_sources"] == ["microphone"]
    assert initial.json()["allowed_actions"] == ["publish"]
    assert replay.status_code == 200
    assert overposted.status_code == 422
    assert "token" not in initial.text
    assert "server_url" not in initial.text


def test_transmit_no_nearby_listener_denial_is_stable_and_non_disclosing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def create(*args: object, **kwargs: object) -> TransmitGrantReceipt:
        del args, kwargs
        raise GrantError(
            "PTT_NO_NEARBY_LISTENERS",
            "No nearby listeners are currently available.",
        )

    monkeypatch.setattr(ptt_api, "create_transmit_grant", create)
    application = authenticated_application()
    receive_grant_id = uuid.uuid4()
    with TestClient(application) as client:
        denied = client.post(
            f"/api/v1/ptt/grants/{receive_grant_id}/transmit",
            json={},
            headers={"Idempotency-Key": IDEMPOTENCY_KEY},
        )

    assert denied.status_code == 409
    assert denied.json()["code"] == "PTT_NO_NEARBY_LISTENERS"
    assert denied.json()["detail"] == "No nearby listeners are currently available."
    assert not any(
        fragment in denied.text
        for fragment in ("recipient", "participant", "distance", "radius", "coordinate")
    )


def test_publication_route_is_exact_metadata_only_and_replay_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 8, 6, 4, tzinfo=UTC)
    transmit_grant_id = uuid.uuid4()
    calls = 0

    async def publish(*args: object, **kwargs: object) -> PublicationReceipt:
        nonlocal calls
        del args, kwargs
        calls += 1
        return PublicationReceipt(
            transmit_grant_id=transmit_grant_id,
            delivery_state="ready",
            proximity_policy_version="proximity-v1",
            evaluated_at=now,
            expires_at=now + timedelta(seconds=30),
            replayed=calls > 1,
        )

    monkeypatch.setattr(ptt_api, "publish_transmit_track", publish)
    application = authenticated_application()
    path = f"/api/v1/ptt/grants/{transmit_grant_id}/publication"
    with TestClient(application) as client:
        initial = client.post(path, json={"track_ref": "track_opaque"})
        replay = client.post(path, json={"track_ref": "track_opaque"})
        overposted = client.post(
            path,
            json={"track_ref": "track_opaque", "participant_refs": ["listener_opaque"]},
        )

    assert initial.status_code == 200
    assert initial.json()["delivery_state"] == "ready"
    assert replay.json()["replayed"] is True
    assert overposted.status_code == 422
    assert set(initial.json()) == {
        "transmit_grant_id",
        "delivery_state",
        "proximity_policy_version",
        "evaluated_at",
        "expires_at",
        "replayed",
    }
    assert not any(
        fragment in initial.text
        for fragment in (
            "recipient",
            "participant",
            "coordinate",
            "distance",
            "radius",
            "count",
            "token",
            "provider",
        )
    )


def test_receive_overposting_and_rate_limit_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 24, 1, tzinfo=UTC)

    async def create(*args: object, **kwargs: object) -> ReceiveGrantReceipt:
        return ReceiveGrantReceipt(
            grant_id=uuid.uuid4(),
            room_ref="rm_opaque",
            participant_ref="pt_opaque",
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
            policy_version="ptt-v1",
            replayed=False,
            server_url="wss://synthetic.invalid",
            participant_token="synthetic-one-time-token",
        )

    monkeypatch.setattr(ptt_api, "create_receive_grant", create)
    application = authenticated_application(receive_limit=1)
    headers = {"Idempotency-Key": IDEMPOTENCY_KEY}

    with TestClient(application) as client:
        overposted = client.post(
            "/api/v1/ptt/grants",
            json={"mode": "receive", "room_ref": "private-room-selector"},
            headers=headers,
        )
        initial = client.post("/api/v1/ptt/grants", json={"mode": "receive"}, headers=headers)
        limited = client.post(
            "/api/v1/ptt/grants",
            json={"mode": "receive"},
            headers={"Idempotency-Key": "synthetic-key-0002"},
        )

    assert overposted.status_code == 422
    assert "private-room-selector" not in overposted.text
    assert initial.status_code == 201
    assert limited.status_code == 429
    assert limited.json()["code"] == "PTT_RATE_LIMITED"
    assert int(limited.headers["Retry-After"]) >= 1


def test_provider_failure_is_stable_and_does_not_disclose_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def reject(*args: object, **kwargs: object) -> ReceiveGrantReceipt:
        raise GrantError("PTT_PROVIDER_UNAVAILABLE", "Receive media is not available.")

    monkeypatch.setattr(ptt_api, "create_receive_grant", reject)
    application = authenticated_application()
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/ptt/grants",
            json={"mode": "receive"},
            headers={"Idempotency-Key": IDEMPOTENCY_KEY},
        )

    assert response.status_code == 503
    assert response.json()["code"] == "PTT_PROVIDER_UNAVAILABLE"
    assert IDEMPOTENCY_KEY not in response.text
    assert "synthetic-livekit-secret" not in response.text
