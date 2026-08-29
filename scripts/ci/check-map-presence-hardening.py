#!/usr/bin/env python3
"""Fail CI when Sprint 8 map/presence privacy, provider, or cost boundaries regress."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 8 map/presence hardening gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return target.read_text(encoding="utf-8")


def require(path: str, *phrases: str) -> None:
    content = " ".join(read(path).lower().split())
    for phrase in phrases:
        if " ".join(phrase.lower().split()) not in content:
            fail(f"{path} is missing required control {phrase!r}")


policy_path = "backend/app/presence/policy.py"
require(
    policy_path,
    "PRESENCE_CELL_SIZE_M = 2_000",
    "PRESENCE_MIN_VISIBLE_ACCOUNTS = 3",
    "PRESENCE_MAX_VISIBLE_CELLS = 32",
    'Literal["few", "several", "many"]',
    "account_cells",
    "account_cells[point.account_key] = None",
)

api_path = "backend/app/api/presence.py"
api = read(api_path)
for required in (
    "PRESENCE_SELECTOR_FORBIDDEN",
    "privacy_min_accounts=PRESENCE_MIN_VISIBLE_ACCOUNTS",
    "approximate_latitude=cell.approximate_latitude",
    "approximate_longitude=cell.approximate_longitude",
    "cell_size_m=PRESENCE_CELL_SIZE_M",
    "density=cell.density",
):
    if required not in api:
        fail(f"{api_path} is missing required privacy response control {required!r}")
for forbidden in (
    "account_count=cell.account_count",
    "account_id=",
    "device_id=",
    "callsign=",
    "distance_m=",
    "bearing",
    "heading",
    "speed",
    "destination",
    "corridor",
    "direction",
):
    if forbidden.lower() in api.lower():
        fail(f"{api_path} exposes forbidden presence field marker {forbidden!r}")

lifecycle = read("backend/app/presence/lifecycle.py").lower()
for required in (
    "currentlocation.expires_at > current_time",
    'currentlocation.quality_state == "usable"',
    "account.status == \"active\"",
    'consent.decision == "granted"',
    "session.revoked_at.is_(none)",
    "session.expires_at > current_time",
    "currentlocation.account_id != viewer_account_id",
):
    if required not in lifecycle:
        fail(f"presence lifecycle is missing current-only eligibility gate {required!r}")
for forbidden in (
    "presencehistory",
    "presence_history",
    "insert(presence",
    "update(presence",
):
    if forbidden in lifecycle:
        fail(f"presence lifecycle contains history/persistence marker {forbidden!r}")

provider_path = "backend/app/map_provider/provider.py"
provider = read(provider_path).lower()
for required in (
    'literal["disabled", "fake"]',
    "deterministic local/ci svg tiles with no network or dataset dependency",
    "map_provider_max_tile_bytes = 32_768",
    "map_provider_timeout_ms = 250",
):
    if required not in provider:
        fail(f"map provider is missing required local-only boundary {required!r}")
for forbidden in (
    "httpx",
    "requests",
    "urllib",
    "socket",
    "mapbox",
    "googlemaps",
    "openstreetmap.org",
    "api_key",
    "api_secret",
    "access_token",
    "billing",
):
    if forbidden in provider:
        fail(f"map provider contains forbidden external-service marker {forbidden!r}")

scale_path = "backend/tests/test_presence_scale.py"
require(
    scale_path,
    "test_presence_at_100_25_10_scale",
    "ACCOUNT_COUNT = 100",
    "VIEWER_COUNT = 25",
    "PUBLISHER_COUNT = 10",
    "TARGET_MS = 400",
    '"lookup_aggregation_p95_ms"',
    '"refresh_p95_ms"',
)

for path in (
    "backend/tests/test_presence_database.py",
    "backend/tests/test_presence_routes.py",
    "backend/tests/test_map_provider.py",
    "backend/tests/test_map_page.py",
    "mobile/src/__tests__/MapAwarenessScreen.test.tsx",
):
    if not (ROOT / path).is_file():
        fail(f"required Sprint 8 regression coverage is missing: {path}")

backend = tomllib.loads(read("backend/pyproject.toml"))
backend_dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0]
    for dependency in backend["project"]["dependencies"]
}
mobile_dependencies = set(json.loads(read("mobile/package.json"))["dependencies"])
prohibited_dependencies = {
    "boto3",
    "celery",
    "redis",
    "requests",
    "httpx",
    "mapbox-gl",
    "react-native-maps",
    "@rnmapbox/maps",
    "@aws-sdk/client-location",
}
unexpected = (backend_dependencies | mobile_dependencies) & prohibited_dependencies
if unexpected:
    fail("unapproved map/cloud/background dependency: " + ", ".join(sorted(unexpected)))

workflow = read(".github/workflows/sprint-8-hardening.yml")
for command in (
    "pytest -q -s tests/test_presence_scale.py",
    "python scripts/ci/check-map-presence-hardening.py",
):
    if command not in workflow:
        fail(f"Sprint 8 hardening CI does not enforce {command!r}")

normal_workflow = read(".github/workflows/ci.yml")
for command in (
    "python scripts/ci/check-location-privacy.py",
    "python scripts/ci/check-proximity-privacy.py",
    "python scripts/ci/check-route-awareness-hardening.py",
    "sh scripts/ci/validate-terraform.sh",
):
    if command not in normal_workflow and "check-route-awareness-hardening.py" not in read(
        ".github/workflows/sprint-7-hardening.yml"
    ):
        fail(f"existing privacy/IaC gate is no longer enforced: {command!r}")

require(
    "docs/evidence/sprint-8/README.md",
    "400 ms p95",
    "100 registered accounts",
    "25 presence viewers",
    "10 active publishers",
    "$0/month",
    "no production map provider selected",
    "license and attribution",
)

print("Sprint 8 map/presence hardening gate: passed")
