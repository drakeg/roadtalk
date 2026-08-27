import asyncio

import pytest
from pydantic import ValidationError

from app.map_provider.provider import (
    MAP_PROVIDER_MAX_TILE_BYTES,
    MAP_PROVIDER_VERSION,
    DisabledMapTileProvider,
    FakeMapTileProvider,
    MapProviderUnavailable,
    MapTile,
    MapTileFetcher,
    MapTileRequest,
    build_map_provider,
)


def test_tile_request_rejects_out_of_range_coordinates() -> None:
    assert MapTileRequest(zoom=0, x=0, y=0).model_dump() == {
        "zoom": 0,
        "x": 0,
        "y": 0,
    }

    with pytest.raises(ValidationError):
        MapTileRequest(zoom=2, x=4, y=0)
    with pytest.raises(ValidationError):
        MapTileRequest(zoom=2, x=0, y=4)
    with pytest.raises(ValidationError):
        MapTileRequest.model_validate({"zoom": 1, "x": 0, "y": 0, "url": "https://example.com"})


def test_fake_provider_is_deterministic_and_local_only() -> None:
    async def exercise() -> None:
        provider = FakeMapTileProvider()
        request = MapTileRequest(zoom=7, x=33, y=48)

        first = await provider.get_tile(request)
        second = await provider.get_tile(request)

        assert first == second
        assert first.provider_version == MAP_PROVIDER_VERSION
        assert first.content_type == "image/svg+xml"
        assert first.attribution == "RoadTalk local map fixture"
        text = first.body.decode("utf-8")
        lower = text.lower()
        assert "RoadTalk local fixture" in text
        assert "z7 / x33 / y48" in text
        assert 'xmlns="http://www.w3.org/2000/svg"' in text
        assert text.count("http://") == 1
        assert "https://" not in text
        assert "href=" not in lower
        assert "src=" not in lower
        assert "api_key" not in lower
        assert "token" not in lower

    asyncio.run(exercise())


def test_disabled_provider_fails_closed() -> None:
    async def exercise() -> None:
        provider = DisabledMapTileProvider()
        with pytest.raises(MapProviderUnavailable, match="map provider unavailable"):
            await provider.get_tile(MapTileRequest(zoom=0, x=0, y=0))

    asyncio.run(exercise())


def test_builder_allows_only_disabled_or_fake() -> None:
    assert isinstance(build_map_provider("disabled"), DisabledMapTileProvider)
    assert isinstance(build_map_provider("fake"), FakeMapTileProvider)

    with pytest.raises(MapProviderUnavailable, match="map provider unavailable"):
        build_map_provider("public")  # type: ignore[arg-type]


def test_fetcher_accepts_valid_local_fixture() -> None:
    async def exercise() -> None:
        fetcher = MapTileFetcher(FakeMapTileProvider())
        tile = await fetcher.get_tile(MapTileRequest(zoom=3, x=2, y=5))
        assert len(tile.body) < MAP_PROVIDER_MAX_TILE_BYTES

    asyncio.run(exercise())


def test_fetcher_fails_closed_on_provider_error() -> None:
    class BrokenProvider:
        async def get_tile(self, request: MapTileRequest) -> MapTile:
            del request
            raise RuntimeError("synthetic provider detail")

    async def exercise() -> None:
        fetcher = MapTileFetcher(BrokenProvider())
        with pytest.raises(MapProviderUnavailable) as error:
            await fetcher.get_tile(MapTileRequest(zoom=0, x=0, y=0))
        assert "synthetic provider detail" not in str(error.value)

    asyncio.run(exercise())


def test_fetcher_rejects_oversized_tile_boundary() -> None:
    with pytest.raises(ValueError, match="approved local boundary"):
        MapTileFetcher(
            FakeMapTileProvider(),
            max_tile_bytes=MAP_PROVIDER_MAX_TILE_BYTES + 1,
        )


def test_tile_schema_rejects_external_content_types_and_metadata() -> None:
    with pytest.raises(ValidationError):
        MapTile.model_validate(
            {
                "content_type": "image/png",
                "provider_version": MAP_PROVIDER_VERSION,
                "attribution": "RoadTalk local map fixture",
                "body": b"x",
            }
        )

    with pytest.raises(ValidationError):
        MapTile.model_validate(
            {
                "body": b"x",
                "provider_url": "https://tiles.example.com/{z}/{x}/{y}",
            }
        )
