import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.identity.avatars import (
    AVATARS,
    AVATAR_CATALOG_VERSION,
    AvatarSelectionError,
    avatar_catalog,
    validate_avatar_selection,
)
from app.identity.service import ProfileMutationError, update_profile
from app.main import create_app


def test_catalog_is_versioned_accessible_and_matches_mobile_bundle() -> None:
    response = avatar_catalog()
    mobile_path = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "identity"
        / "avatarCatalog.json"
    )
    mobile = json.loads(mobile_path.read_text(encoding="utf-8"))

    assert response.version == AVATAR_CATALOG_VERSION == mobile["version"]
    assert [
        {
            "id": avatar.id,
            "label": avatar.label,
            "glyph": avatar.glyph,
            "background_color": avatar.background_color,
            "foreground_color": avatar.foreground_color,
            "status": avatar.status,
        }
        for avatar in AVATARS
    ] == mobile["avatars"]
    assert len({avatar.id for avatar in AVATARS}) == len(AVATARS)
    assert all(avatar.label.endswith(" avatar") for avatar in AVATARS)


def test_active_avatar_is_selectable_but_retired_and_unknown_fail_closed() -> None:
    assert validate_avatar_selection("road-runner").status == "active"

    for avatar_id in ("classic-rig", "unknown"):
        with pytest.raises(AvatarSelectionError):
            validate_avatar_selection(avatar_id)


def test_avatar_catalog_route_is_static_and_public() -> None:
    application = create_app(
        Settings(
            environment="test",
            docs_enabled=True,
            log_level="CRITICAL",
            database_check_enabled=False,
        )
    )
    with TestClient(application) as client:
        response = client.get("/api/v1/avatars")
        schema = client.get("/openapi.json").json()

    assert response.status_code == 200
    assert response.json()["version"] == AVATAR_CATALOG_VERSION
    assert len(response.json()["avatars"]) == len(AVATARS)
    assert "security" not in schema["paths"]["/api/v1/avatars"]["get"]


def test_retired_avatar_update_fails_before_database_access() -> None:
    db = AsyncMock()

    with pytest.raises(ProfileMutationError) as raised:
        asyncio.run(
            update_profile(
                db,
                account_id=__import__("uuid").uuid4(),
                candidate="Road-Runner",
                avatar_id="classic-rig",
                expected_version=0,
                cooldown_seconds=0,
            )
        )

    assert raised.value.code == "AVATAR_UNAVAILABLE"
    db.scalar.assert_not_awaited()
