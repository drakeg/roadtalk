#!/usr/bin/env python3
"""Fail CI when approved Sprint 7 planning loses a safety boundary."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 7 planning gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


specification = "docs/sprints/sprint-7-route-awareness.md"
spec = read(specification)
for identifier in (
    *(f"s07-r{index:02d}" for index in range(1, 13)),
    *(f"s07-t{index:02d}" for index in range(1, 13)),
    *(f"s07-d{index:02d}" for index in range(1, 10)),
):
    if identifier not in spec:
        fail(f"{specification} does not define {identifier.upper()}")

for phrase in (
    "approved for implementation in locked tracker issue #173",
    "nearby remains the default",
    "same road is an explicit account setting",
    "does not ask for or infer a destination",
    "automatic subscription",
    "deterministic fixtures and a fake provider",
    "real map data",
    "fail same-road closed",
    "100-account/25-receiver/10-publisher",
    "$0 aws + $0 livekit + $0 routing provider per month",
    "no public osrm endpoint",
    "before sprint 8 planning",
):
    if phrase not in spec:
        fail(f"{specification} is missing {phrase!r}")

readiness_path = "docs/sprints/sprint-7-readiness.md"
readiness = read(readiness_path)
for phrase in (
    "approved for locked local/ci implementation",
    "nearby remains the default",
    "same road is an explicit restrictive receive mode",
    "real provider configuration must remain disabled",
    "cannot turn a prior denial into eligibility",
    "one `current_route_context` row",
    "odbl attribution/share-alike",
    "terraform | disabled; zero resources",
    "ready to code within the locked local/ci boundary",
):
    if phrase not in readiness:
        fail(f"{readiness_path} is missing {phrase!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-sprint-7-planning.py" not in workflow:
    fail("CI does not enforce the Sprint 7 planning gate")
if "check approved sprint 7 planning boundaries" not in workflow:
    fail("CI does not describe Sprint 7 planning as approved")

print("Sprint 7 planning gate: passed")
