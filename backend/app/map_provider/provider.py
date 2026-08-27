from __future__ import annotations

import asyncio
import html
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAP_PROVIDER_VERSION = "local-fixture-v1"
MAP_PROVIDER_MAX_TILE_BYTES = 32_768
MAP_PROVIDER_TIMEOUT_MS = 250


class MapTileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    zoom: int = Field(ge=0, le=18)
    x: int = Field(ge=0)
    y: int = Field(ge=0)

    @model_validator(mode="after")
    def tile_coordinates_must_fit_zoom(self) -> MapTileRequest:
        upper_bound = 1 << self.zoom
        if self.x >= upper_bound or self.y >= upper_bound:
            raise ValueError("tile coordinate is outside the requested zoom")
        return self


class MapTile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    content_type: Literal["image/svg+xml"] = "image/svg+xml"
    provider_version: Literal["local-fixture-v1"] = MAP_PROVIDER_VERSION
    attribution: Literal["RoadTalk local map fixture"] = "RoadTalk local map fixture"
    body: bytes = Field(min_length=1, max_length=MAP_PROVIDER_MAX_TILE_BYTES)


class MapProviderError(RuntimeError):
    """Stable non-disclosing map-provider failure."""


class MapProviderUnavailable(MapProviderError):
    """Map provider is disabled or could not return a safe local tile."""


class MapTileProvider(Protocol):
    async def get_tile(self, request: MapTileRequest) -> MapTile: ...


@dataclass(frozen=True, slots=True)
class FakeMapStyle:
    background: str = "#101820"
    grid: str = "#32404a"
    text: str = "#d6e1e8"


class FakeMapTileProvider:
    """Deterministic local/CI SVG tiles with no network or dataset dependency."""

    def __init__(self, style: FakeMapStyle | None = None) -> None:
        self._style = style or FakeMapStyle()

    async def get_tile(self, request: MapTileRequest) -> MapTile:
        label = html.escape(f"z{request.zoom} / x{request.x} / y{request.y}")
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" '
            'viewBox="0 0 256 256" role="img" aria-label="Local map fixture">'
            f'<rect width="256" height="256" fill="{self._style.background}"/>'
            f'<path d="M0 64H256M0 128H256M0 192H256M64 0V256M128 0V256M192 0V256" '
            f'stroke="{self._style.grid}" stroke-width="1"/>'
            f'<text x="128" y="128" text-anchor="middle" fill="{self._style.text}" '
            'font-family="sans-serif" font-size="14">RoadTalk local fixture</text>'
            f'<text x="128" y="150" text-anchor="middle" fill="{self._style.text}" '
            f'font-family="monospace" font-size="12">{label}</text>'
            "</svg>"
        )
        return MapTile(body=svg.encode("utf-8"))


class DisabledMapTileProvider:
    async def get_tile(self, request: MapTileRequest) -> MapTile:
        del request
        raise MapProviderUnavailable("map provider unavailable")


class MapTileFetcher:
    """Timeout and integrity boundary around configured map providers."""

    def __init__(
        self,
        provider: MapTileProvider,
        *,
        timeout_ms: int = MAP_PROVIDER_TIMEOUT_MS,
        max_tile_bytes: int = MAP_PROVIDER_MAX_TILE_BYTES,
    ) -> None:
        if timeout_ms < 1 or timeout_ms > 2_000:
            raise ValueError("map provider timeout must be between 1 and 2000 ms")
        if max_tile_bytes < 1 or max_tile_bytes > MAP_PROVIDER_MAX_TILE_BYTES:
            raise ValueError("map provider tile limit is outside the approved local boundary")
        self._provider = provider
        self._timeout_seconds = timeout_ms / 1_000
        self._max_tile_bytes = max_tile_bytes

    async def get_tile(self, request: MapTileRequest) -> MapTile:
        try:
            tile = await asyncio.wait_for(
                self._provider.get_tile(request),
                timeout=self._timeout_seconds,
            )
        except Exception:
            raise MapProviderUnavailable("map provider unavailable") from None

        if tile.content_type != "image/svg+xml":
            raise MapProviderUnavailable("map provider unavailable")
        if tile.provider_version != MAP_PROVIDER_VERSION:
            raise MapProviderUnavailable("map provider unavailable")
        if len(tile.body) > self._max_tile_bytes:
            raise MapProviderUnavailable("map provider unavailable")
        return tile


def build_map_provider(provider: Literal["disabled", "fake"] = "disabled") -> MapTileProvider:
    if provider == "disabled":
        return DisabledMapTileProvider()
    if provider == "fake":
        return FakeMapTileProvider()
    raise MapProviderUnavailable("map provider unavailable")
