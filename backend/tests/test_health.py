import pytest

from app.health import ReadinessRegistry


@pytest.mark.anyio
async def test_registry_reports_ready_and_not_ready() -> None:
    registry = ReadinessRegistry()

    async def healthy() -> None:
        return None

    async def unhealthy() -> None:
        raise RuntimeError("dependency unavailable")

    registry.register("healthy", healthy)
    registry.register("unhealthy", unhealthy)

    assert await registry.evaluate() == {
        "healthy": "ready",
        "unhealthy": "not_ready",
    }


def test_registry_rejects_duplicate_names() -> None:
    registry = ReadinessRegistry()

    async def check() -> None:
        return None

    registry.register("database", check)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("database", check)
