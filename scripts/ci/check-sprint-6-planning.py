#!/usr/bin/env python3
"""Fail CI when approved Sprint 6 planning loses a locked safety boundary."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 6 planning gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


specification = "docs/sprints/sprint-6-channels.md"
spec = read(specification)
for identifier in (
    *(f"s06-r{index:02d}" for index in range(1, 13)),
    *(f"s06-t{index:02d}" for index in range(1, 13)),
    *(f"s06-d{index:02d}" for index in range(1, 10)),
):
    if identifier not in spec:
        fail(f"{specification} does not define {identifier.upper()}")

for phrase in (
    "approved for local/github ci implementation — product-owner approved on 2026-08-14",
    "through issue #129",
    "locked tracker #139",
    "general and rv are server-seeded",
    "high-entropy invite secret",
    "exactly one selected active channel",
    "automatic subscription remains disabled",
    "does not use livekit's cloud-only moveparticipant operation",
    "100 registered accounts, 25 connected receivers, and 10 active publishers",
    "current and incremental recurring cost is **$0 aws + $0 livekit per month**",
    "no aws resource or paid/managed capability",
    "before sprint 7 planning",
):
    if phrase not in spec:
        fail(f"{specification} is missing {phrase!r}")

readiness_path = "docs/sprints/sprint-6-readiness.md"
readiness = read(readiness_path)
for phrase in (
    "status: ready — approved for local/github ci implementation",
    "product owner approved the specification",
    "through issue #129",
    "tracker #139",
    "plaintext is returned once and never stored",
    "room metadata is visible to participants",
    "s01-e01 through s01-e03 remain field-test blockers",
    "terraform | disabled; zero resources",
    "alerts, budgets, and quotas are not automatic shutdown controls",
    "**ready.**",
):
    if phrase not in readiness:
        fail(f"{readiness_path} is missing {phrase!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-sprint-6-planning.py" not in workflow:
    fail("CI does not enforce the Sprint 6 planning gate")
if "check approved sprint 6 planning boundaries" not in workflow:
    fail("CI does not describe Sprint 6 planning as approved")

print("Sprint 6 planning gate: passed")
