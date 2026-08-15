import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import channels as channels_api
from app.api.auth import current_session
from app.auth.service import AuthenticatedSession
from app.channels.constants import GENERAL_CHANNEL_ID, RV_CHANNEL_ID
from app.channels.service import (
    ChannelError,
    ChannelLifecycleReceipt,
    ChannelSelectionReceipt,
    ChannelSummary,
    PrivateChannelReceipt,
)
from app.config import Settings
from app.db.models import Account, Device, Session
from app.db.session import get_session
from app.main import create_app


def settings() -> Settings:
    return Settings(
        environment="test",
        docs_enabled=True,
        log_level="CRITICAL",
        database_check_enabled=False,
    )


def identity() -> AuthenticatedSession:
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="ios",
        installation_id="channel-route-synthetic",
    )
    session = Session(
        id=uuid.uuid4(),
        account=account,
        device=device,
        refresh_token_hash="synthetic-hash",
        expires_at=datetime(2026, 8, 1),
    )
    return AuthenticatedSession(account=account, device=device, session=session)


def authenticated_application() -> FastAPI:
    application = create_app(settings())
    current = identity()
    db = cast(AsyncSession, MagicMock())

    async def override_current() -> AuthenticatedSession:
        return current

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield db

    application.dependency_overrides[current_session] = override_current
    application.dependency_overrides[get_session] = override_db
    return application


def summary(
    *,
    channel_id: uuid.UUID = GENERAL_CHANNEL_ID,
    slug: str | None = "general",
    label: str = "General",
    selected: bool = True,
) -> ChannelSummary:
    return ChannelSummary(
        id=channel_id,
        slug=slug,
        display_label=label,
        type="public",
        selected=selected,
        enabled=True,
        version=1,
    )


def selection(
    *,
    channel_id: uuid.UUID = GENERAL_CHANNEL_ID,
    slug: str = "general",
    label: str = "General",
    version: int = 1,
) -> ChannelSelectionReceipt:
    return ChannelSelectionReceipt(
        **summary(channel_id=channel_id, slug=slug, label=label).__dict__,
        selected_at=datetime(2026, 8, 14, 12, tzinfo=UTC),
        selection_version=version,
    )


def test_channel_openapi_is_authenticated_exact_and_non_disclosing() -> None:
    schema = create_app(settings()).openapi()
    catalog = schema["paths"]["/api/v1/channels"]["get"]
    current = schema["paths"]["/api/v1/me/channel"]["get"]
    select = schema["paths"]["/api/v1/channels/{channel_id}/select"]["post"]

    for operation in (catalog, current, select):
        assert operation["security"] == [{"HTTPBearer": []}]
        assert operation["tags"] == ["channels"]
    assert "requestBody" not in select

    components = schema["components"]["schemas"]
    assert set(components["ChannelSummaryResponse"]["properties"]) == {
        "id",
        "slug",
        "display_label",
        "type",
        "selected",
        "enabled",
        "version",
    }
    assert set(components["ChannelSelectionResponse"]["properties"]) == {
        "id",
        "slug",
        "display_label",
        "type",
        "selected",
        "enabled",
        "version",
        "selected_at",
        "selection_version",
    }
    serialized = str(
        {
            "summary": components["ChannelSummaryResponse"],
            "selection": components["ChannelSelectionResponse"],
            "catalog": components["ChannelCatalogResponse"],
        }
    ).lower()
    for forbidden in (
        "member_count",
        "members",
        "owner_id",
        "creator_account_id",
        "provider_room_ref",
        "invite",
        "participant",
    ):
        assert forbidden not in serialized


def test_channel_routes_require_bearer_authentication() -> None:
    application = create_app(settings())
    with TestClient(application, raise_server_exceptions=False) as client:
        responses = (
            client.get("/api/v1/channels"),
            client.get("/api/v1/me/channel"),
            client.post(f"/api/v1/channels/{RV_CHANNEL_ID}/select"),
        )

    assert {response.status_code for response in responses} == {401}
    assert {response.json()["code"] for response in responses} == {"AUTHENTICATION_REQUIRED"}


def test_catalog_and_selection_return_semantic_channel_metadata_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def catalog(*args: object, **kwargs: object) -> tuple[ChannelSummary, ...]:
        del args, kwargs
        return (
            summary(),
            summary(
                channel_id=RV_CHANNEL_ID,
                slug="rv",
                label="RV",
                selected=False,
            ),
        )

    async def current(*args: object, **kwargs: object) -> ChannelSelectionReceipt:
        del args, kwargs
        return selection()

    async def select(*args: object, **kwargs: object) -> ChannelSelectionReceipt:
        del args, kwargs
        return selection(channel_id=RV_CHANNEL_ID, slug="rv", label="RV", version=2)

    monkeypatch.setattr(channels_api, "list_channels", catalog)
    monkeypatch.setattr(channels_api, "get_current_channel", current)
    monkeypatch.setattr(channels_api, "select_channel", select)
    application = authenticated_application()

    with TestClient(application) as client:
        listed = client.get("/api/v1/channels")
        selected = client.get("/api/v1/me/channel")
        switched = client.post(f"/api/v1/channels/{RV_CHANNEL_ID}/select")

    assert [item["slug"] for item in listed.json()["items"]] == ["general", "rv"]
    assert selected.json()["slug"] == "general"
    assert switched.json()["slug"] == "rv"
    assert switched.json()["selection_version"] == 2
    combined = listed.text + selected.text + switched.text
    for forbidden in (
        "channel-route-synthetic",
        "provider_room",
        "member_count",
        "creator",
        "participant",
        "invite",
    ):
        assert forbidden not in combined


@pytest.mark.parametrize(
    ("code", "expected_status"),
    [
        ("CHANNEL_NOT_AVAILABLE", 404),
        ("CHANNEL_MEDIA_ACTIVE", 409),
        ("CHANNEL_DEFAULT_UNAVAILABLE", 409),
    ],
)
def test_channel_failures_are_stable_and_non_disclosing(
    monkeypatch: pytest.MonkeyPatch,
    code: str,
    expected_status: int,
) -> None:
    async def reject(*args: object, **kwargs: object) -> ChannelSelectionReceipt:
        del args, kwargs
        raise ChannelError(code, "The channel is not available.")

    monkeypatch.setattr(channels_api, "select_channel", reject)
    application = authenticated_application()
    with TestClient(application) as client:
        response = client.post(f"/api/v1/channels/{uuid.uuid4()}/select")

    assert response.status_code == expected_status
    assert response.json()["code"] == code
    for forbidden in ("member", "owner", "creator", "room", "participant", "invite"):
        assert forbidden not in response.text


def test_private_lifecycle_routes_return_only_approved_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    channel_id = uuid.uuid4()
    changed_at = datetime(2026, 8, 15, 12, tzinfo=UTC)
    invite = "rtc1." + "a" * 43

    async def private_receipt(*args: object, **kwargs: object) -> PrivateChannelReceipt:
        del args, kwargs
        return PrivateChannelReceipt(
            id=channel_id,
            slug=None,
            display_label="Camp Friends",
            type="private",
            selected=False,
            enabled=True,
            version=1,
            created_at=changed_at,
            invite=invite,
        )

    async def lifecycle(*args: object, **kwargs: object) -> ChannelLifecycleReceipt:
        del args, kwargs
        return ChannelLifecycleReceipt(channel_id, "joined", changed_at, False)

    async def left(*args: object, **kwargs: object) -> ChannelLifecycleReceipt:
        del args, kwargs
        return ChannelLifecycleReceipt(channel_id, "left", changed_at, False)

    async def closed(*args: object, **kwargs: object) -> ChannelLifecycleReceipt:
        del args, kwargs
        return ChannelLifecycleReceipt(channel_id, "closed", changed_at, True)

    monkeypatch.setattr(channels_api, "create_private_channel", private_receipt)
    monkeypatch.setattr(channels_api, "join_private_channel", lifecycle)
    monkeypatch.setattr(channels_api, "leave_private_channel", left)
    monkeypatch.setattr(channels_api, "rotate_private_invite", private_receipt)
    monkeypatch.setattr(channels_api, "close_private_channel", closed)
    application = authenticated_application()

    with TestClient(application) as client:
        created = client.post(
            "/api/v1/channels/private",
            json={"display_label": "Camp Friends"},
            headers={"Idempotency-Key": "create-private-0001"},
        )
        joined = client.post("/api/v1/channels/private/join", json={"invite": invite})
        left_response = client.delete(f"/api/v1/channels/{channel_id}/membership")
        rotated = client.post(
            f"/api/v1/channels/{channel_id}/invite/rotation",
            headers={"Idempotency-Key": "rotate-private-0001"},
        )
        closed_response = client.delete(f"/api/v1/channels/{channel_id}")

    assert created.status_code == 201
    assert created.json()["invite"] == invite
    assert joined.json()["state"] == "joined"
    assert left_response.json()["state"] == "left"
    assert rotated.json()["invite"] == invite
    assert closed_response.json() == {
        "channel_id": str(channel_id),
        "state": "closed",
        "changed_at": changed_at.isoformat().replace("+00:00", "Z"),
        "replayed": True,
    }
