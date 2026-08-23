#!/usr/bin/env python3
"""Fail CI if the Sprint 7 route-context provider boundary broadens."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 7 route-context provider gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


provider = read("backend/app/route_context/provider.py")
for phrase in (
    "class routecontextmatchrequest",
    'extra="forbid"',
    "class fakeroutecontextprovider",
    "class disabledroutecontextprovider",
    "asyncio.wait_for",
    "source_location_version",
    "provider_corridor_ref",
    "route context unavailable",
):
    if phrase not in provider:
        fail(f"provider boundary is missing {phrase!r}")

for forbidden in (
    "httpx",
    "requests",
    "urllib",
    "socket",
    "osrm",
    "openstreetmap",
    "boto3",
    "api_key",
    "api_secret",
    "access_token",
):
    if forbidden in provider:
        fail(f"provider boundary contains forbidden external-service marker {forbidden!r}")

config = read("backend/app/config.py")
for phrase in (
    'route_context_provider: literal["disabled", "fake"] = "disabled"',
    "route_context_timeout_ms",
    "route_context_ttl_seconds",
    'self.environment in {"field-test", "production"}',
):
    if phrase not in config:
        fail(f"route-context configuration is missing {phrase!r}")

for forbidden in (
    "route_context_url",
    "route_context_api_key",
    "route_context_api_secret",
    "route_context_token",
):
    if forbidden in config:
        fail(f"route-context configuration contains forbidden credential/network field {forbidden!r}")

env_example = read(".env.example")
if "roadtalk_route_context_provider=disabled" not in env_example:
    fail("example environment must keep route-context matching disabled by default")

provider_tests = read("backend/tests/test_route_context_provider.py")
for phrase in (
    "raw_provider_payload",
    "slowprovider",
    'route_context_provider="osrm"',
    'environment="production"',
):
    if phrase not in provider_tests:
        fail(f"provider tests are missing boundary evidence {phrase!r}")

print("Sprint 7 route-context provider gate: passed")
