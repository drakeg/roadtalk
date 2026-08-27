#!/usr/bin/env python3
"""Fail CI when Sprint 7 route-awareness hardening or evidence regresses."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 7 route-awareness hardening gate: {message}", file=sys.stderr)
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


scale = "backend/tests/test_route_awareness_scale.py"
require(
    scale,
    "test_route_awareness_control_plane_at_100_25_10_scale",
    '"registered_accounts": 100',
    '"connected_receivers": 25',
    '"active_publishers": 10',
    '"nearby_eligible_p95_ms"',
    '"same_road_eligible_p95_ms"',
    '"same_road_zero_recipient_p95_ms"',
    '"reconciliation_p95_ms"',
    "target_ms = 400",
    "corridor_a",
    "corridor_b",
    "corridor_c",
)

required_tests = {
    "backend/tests/test_ptt_proximity.py": (
        "test_same_road_direction_policy_is_coarse_and_wraparound_safe",
        "test_same_road_filter_can_only_reduce_prior_eligibility",
        "denied_before_route_filter",
        "stationary",
        "unknown",
    ),
    "backend/tests/test_route_context_provider.py": (
        "raw_provider_payload",
        "slowprovider",
        'route_context_provider="osrm"',
        'environment="production"',
    ),
    "backend/tests/test_route_context_lifecycle_database.py": (
        "corridor_digest",
        "source_location_version",
        "provider_corridor_ref",
    ),
    "backend/tests/test_logging.py": (
        "route_context.unavailable",
        "eligibility_reason",
        "provider_corridor_ref",
    ),
    "mobile/src/__tests__/RouteModeScreen.test.tsx": (
        "does not expose route details in user-visible copy",
        "same road is unavailable right now",
    ),
}
for path, phrases in required_tests.items():
    content = read(path).lower()
    for phrase in phrases:
        if phrase.lower() not in content:
            fail(f"{path} is missing required route hardening coverage {phrase!r}")

provider = read("backend/app/route_context/provider.py").lower()
for forbidden in (
    "httpx",
    "requests",
    "urllib",
    "socket",
    "openstreetmap",
    "project-osrm",
    "api_key",
    "api_secret",
    "access_token",
):
    if forbidden in provider:
        fail(f"route provider contains forbidden external-service marker {forbidden!r}")

config = " ".join(read("backend/app/config.py").lower().split())
if 'route_context_provider: literal["disabled", "fake"] = "disabled"' not in config:
    fail("route-context provider must remain disabled/fake only")
for forbidden in (
    "route_context_url",
    "route_context_api_key",
    "route_context_api_secret",
    "route_context_token",
):
    if forbidden in config:
        fail(f"route-context config contains forbidden external field {forbidden!r}")

env_example = read(".env.example").lower()
if "roadtalk_route_context_provider=disabled" not in env_example:
    fail("example environment must keep real route matching disabled")

route_model = read("backend/app/route_context/models.py").lower()
for required in (
    "corridor_digest",
    "direction",
    "confidence",
    "source_location_version",
    "provider_version",
    "policy_version",
    "matched_at",
    "expires_at",
):
    if required not in route_model:
        fail(f"current route context model is missing {required!r}")
for forbidden in (
    "road_name",
    "snapped",
    "geometry",
    "polyline",
    "destination",
    "itinerary",
    "provider_payload",
):
    if forbidden in route_model:
        fail(f"current route context model contains prohibited field marker {forbidden!r}")

evidence = "docs/evidence/sprint-7/README.md"
require(
    evidence,
    "current and incremental cost: **$0/month**",
    "external routing/map calls or dataset downloads: **none**",
    "live-provider, physical-device, and field status: **not performed**",
    "open database license (odbl) attribution obligations",
    "share-alike obligations",
    "control-plane target: **400 ms p95**",
    "nearby eligible lookup p95: **40.71 ms**",
    "same-road eligible lookup p95: **24.03 ms**",
    "same-road zero-recipient denial p95: **18.97 ms**",
    "bounded publication/subscription reconciliation p95: **160.94 ms**",
    "no free public osm or osrm service is assumed to be production infrastructure",
    "cross-browser/physical-system verification remains a field exception",
)

backend = tomllib.loads(read("backend/pyproject.toml"))
backend_dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0]
    for dependency in backend["project"]["dependencies"]
}
mobile_dependencies = set(json.loads(read("mobile/package.json"))["dependencies"])
prohibited_dependencies = {
    "boto3",
    "celery",
    "osrm",
    "redis",
    "requests",
    "httpx",
    "@aws-sdk/client-rds",
    "@aws-sdk/client-sqs",
}
unexpected = (backend_dependencies | mobile_dependencies) & prohibited_dependencies
if unexpected:
    fail("unapproved route/cloud/later-sprint dependency: " + ", ".join(sorted(unexpected)))

hardening_workflow = read(".github/workflows/sprint-7-hardening.yml")
for command in (
    "pytest -q -s tests/test_route_awareness_scale.py",
    "python scripts/ci/check-route-awareness-hardening.py",
):
    if command not in hardening_workflow:
        fail(f"Sprint 7 hardening CI does not enforce {command!r}")

normal_workflow = read(".github/workflows/ci.yml")
for command in (
    "python scripts/ci/check-route-context-provider.py",
    "python scripts/ci/check-route-mode-privacy.py",
    "sh scripts/ci/validate-terraform.sh",
):
    if command not in normal_workflow:
        fail(f"normal CI does not enforce {command!r}")

print("Sprint 7 route-awareness hardening gate: passed")
