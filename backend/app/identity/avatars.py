from dataclasses import dataclass
from typing import Literal

from app.identity.schemas import AvatarCatalogItem, AvatarCatalogResponse

AVATAR_CATALOG_VERSION = "2026.1"


@dataclass(frozen=True, slots=True)
class AvatarDefinition:
    id: str
    label: str
    glyph: str
    background_color: str
    foreground_color: str
    status: Literal["active", "retired"]


AVATARS = (
    AvatarDefinition(
        id="road-runner",
        label="Orange horizon avatar",
        glyph="RR",
        background_color="#9C3D10",
        foreground_color="#FFFFFF",
        status="active",
    ),
    AvatarDefinition(
        id="night-owl",
        label="Indigo night avatar",
        glyph="NO",
        background_color="#273469",
        foreground_color="#FFFFFF",
        status="active",
    ),
    AvatarDefinition(
        id="pine-trail",
        label="Green pine trail avatar",
        glyph="PT",
        background_color="#1F6B4F",
        foreground_color="#FFFFFF",
        status="active",
    ),
    AvatarDefinition(
        id="desert-sun",
        label="Amber desert sun avatar",
        glyph="DS",
        background_color="#8A4B08",
        foreground_color="#FFFFFF",
        status="active",
    ),
    AvatarDefinition(
        id="lake-wave",
        label="Blue lake wave avatar",
        glyph="LW",
        background_color="#075985",
        foreground_color="#FFFFFF",
        status="active",
    ),
    AvatarDefinition(
        id="mountain-pass",
        label="Slate mountain pass avatar",
        glyph="MP",
        background_color="#4B5563",
        foreground_color="#FFFFFF",
        status="active",
    ),
    AvatarDefinition(
        id="classic-rig",
        label="Brown classic rig avatar",
        glyph="CR",
        background_color="#5B3A29",
        foreground_color="#FFFFFF",
        status="retired",
    ),
)

_AVATARS_BY_ID = {avatar.id: avatar for avatar in AVATARS}


class AvatarSelectionError(ValueError):
    pass


def avatar_catalog() -> AvatarCatalogResponse:
    return AvatarCatalogResponse(
        version=AVATAR_CATALOG_VERSION,
        avatars=[
            AvatarCatalogItem(
                id=avatar.id,
                label=avatar.label,
                glyph=avatar.glyph,
                background_color=avatar.background_color,
                foreground_color=avatar.foreground_color,
                status=avatar.status,
                selectable=avatar.status == "active",
            )
            for avatar in AVATARS
        ],
    )


def validate_avatar_selection(avatar_id: str) -> AvatarDefinition:
    avatar = _AVATARS_BY_ID.get(avatar_id)
    if avatar is None or avatar.status != "active":
        raise AvatarSelectionError("This avatar is unavailable.")
    return avatar
