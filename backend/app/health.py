from collections.abc import Awaitable, Callable
from dataclasses import dataclass

HealthCheck = Callable[[], Awaitable[None]]


@dataclass(frozen=True)
class RegisteredCheck:
    name: str
    check: HealthCheck


class ReadinessRegistry:
    def __init__(self) -> None:
        self._checks: list[RegisteredCheck] = []

    def register(self, name: str, check: HealthCheck) -> None:
        if any(existing.name == name for existing in self._checks):
            raise ValueError(f"Readiness check already registered: {name}")
        self._checks.append(RegisteredCheck(name=name, check=check))

    async def evaluate(self) -> dict[str, str]:
        results: dict[str, str] = {}
        for registered in self._checks:
            try:
                await registered.check()
                results[registered.name] = "ready"
            except Exception:
                results[registered.name] = "not_ready"
        return results
