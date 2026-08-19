#!/usr/bin/env python3
"""Fail CI when S06-D08 hardening, scale, operations, or evidence regresses."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Channel hardening gate: {message}", file=sys.stderr)
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


scale = "backend/tests/test_channel_scale.py"
require(
    scale,
    "test_channel_control_plane_at_100_25_10_scale",
    '"registered_accounts": 100',
    '"connected_receivers": 25',
    '"active_publishers": 10',
    '"eligible_p95_ms"',
    '"cross_channel_denied_p95_ms"',
    '"selection_switch_p95_ms"',
    '"invite_verify_p95_ms"',
    '"reconciliation_p95_ms"',
    "target_ms = 400",
    "general_channel_id",
    "rv_channel_id",
    "private_channel_id",
)

required_tests = {
    "backend/tests/test_channel_database.py": (
        "test_channel_catalog_selection_concurrency_and_grant_binding",
        "test_private_channel_invite_lifecycle",
        "channel_media_active",
        "channel_not_available",
    ),
    "backend/tests/test_channel_security.py": (
        "test_invite_is_high_entropy_slow_hashed_and_fingerprinted",
        "test_invite_limiter_covers_peer_and_account",
    ),
    "backend/tests/test_ptt_proximity_database.py": (
        "test_proximity_query_enforces_complete_private_receiver_matrix",
        "selected_channel_id",
        "rv_channel_id",
    ),
    "mobile/src/__tests__/ChannelController.test.ts": (
        "preparechanneltransition",
        "completechanneltransition",
        "provider room secret",
    ),
}
for path, names in required_tests.items():
    content = read(path).lower()
    for name in names:
        if name.lower() not in content:
            fail(f"{path} is missing required channel hardening coverage {name!r}")

operations = "docs/runbooks/channel-operations.md"
require(
    operations,
    "current and incremental cost: **$0 aws + $0 livekit per month**",
    "100 registered accounts, 25 connected receivers, and 10 active publishers",
    "400 ms control-plane target",
    "cross-channel",
    "no budget alert or ci check is an automatic shutdown control",
    "s01-e01 through s01-e03 remain field-test blockers",
)

evidence = "docs/evidence/sprint-6/README.md"
require(
    evidence,
    "current and incremental cost: **$0/month**",
    "aws/livekit resources created: none",
    "live-provider, physical-device, and cloud status: **not performed**",
    "eligible, cross-channel denied, selection/switch, invite verification, and reconciliation p95",
    "alerts and ci gates are not automatic shutdown controls",
)

backend = tomllib.loads(read("backend/pyproject.toml"))
backend_dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0]
    for dependency in backend["project"]["dependencies"]
}
mobile_dependencies = set(json.loads(read("mobile/package.json"))["dependencies"])
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
    "pytest -q -s tests/test_channel_scale.py",
    "python scripts/ci/check-channel-hardening.py",
    "sh scripts/ci/validate-terraform.sh",
):
    if command not in workflow:
        fail(f"CI does not enforce {command!r}")

print("Channel hardening gate: passed")
