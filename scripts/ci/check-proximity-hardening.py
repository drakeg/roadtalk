#!/usr/bin/env python3
"""Fail CI when S05-D08 hardening, scale, operations, or evidence regresses."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Proximity hardening gate: {message}", file=sys.stderr)
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


scale = "backend/tests/test_ptt_proximity_scale.py"
require(
    scale,
    "100",
    "25",
    "10",
    '"eligible_p95_ms"',
    '"denied_p95_ms"',
    '"empty_audience_p95_ms"',
    '"reconciliation_p95_ms"',
    "target_ms = 400",
    "find_eligible_receive_grants",
    "reconcile_proximity_delivery",
)

required_tests = {
    "backend/tests/test_ptt_proximity_database.py": (
        "test_proximity_query_enforces_complete_private_receiver_matrix",
        "test_proximity_boundary_high_latitude_and_antimeridian_are_inclusive",
    ),
    "backend/tests/test_ptt_publication_service.py": (
        "test_publication_replay_is_provider_free_and_conflicting_track_fails_closed",
        "test_publication_provider_failure_compensates_and_marks_reconciling",
    ),
    "backend/tests/test_ptt_proximity_reconciliation.py": (
        "test_unknown_or_provider_degraded_state_stays_pending_and_fail_closed",
        "test_reconciliation_rejects_unbounded_work",
    ),
    "mobile/src/__tests__/PushToTalkController.test.ts": (
        "delivery_reconciling",
        "nearby_unavailable",
        "logout",
    ),
}
for path, names in required_tests.items():
    content = read(path)
    for name in names:
        if name not in content:
            fail(f"{path} is missing required failure/lifecycle coverage {name!r}")

operations = "docs/runbooks/proximity-operations.md"
require(
    operations,
    "current and incremental cost: **$0 aws + $0 livekit per month**",
    "100 accounts, 25 connected receivers, and 10 active publishers",
    "400 ms control-plane target",
    "no budget alert or ci check is an automatic shutdown control",
    "s01-e01 through s01-e03 remain field-test blockers",
)

evidence = "docs/evidence/sprint-5/README.md"
require(
    evidence,
    "current and incremental cost: **$0/month**",
    "aws/livekit resources created: none",
    "live-provider, physical-device, and cloud status: **not performed**",
    "eligible, denied, empty-audience, and reconciliation p95",
    "alerts and ci gates are not automatic shutdown controls",
)

backend = tomllib.loads(read("backend/pyproject.toml"))
backend_dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0]
    for dependency in backend["project"]["dependencies"]
}
mobile_dependencies = set(__import__("json").loads(read("mobile/package.json"))["dependencies"])
prohibited = {
    "boto3",
    "celery",
    "livekit",
    "redis",
    "sentry-sdk",
    "@aws-sdk/client-rds",
    "@aws-sdk/client-sqs",
}
unexpected = (backend_dependencies | mobile_dependencies) & prohibited
if unexpected:
    fail("unapproved paid/later-sprint dependency: " + ", ".join(sorted(unexpected)))

workflow = read(".github/workflows/ci.yml")
for command in (
    "pytest -q -s tests/test_ptt_proximity_scale.py",
    "python scripts/ci/check-proximity-hardening.py",
    "sh scripts/ci/validate-terraform.sh",
):
    if command not in workflow:
        fail(f"CI does not enforce {command!r}")

print("Proximity hardening gate: passed")
