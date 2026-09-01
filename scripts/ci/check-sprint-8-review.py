#!/usr/bin/env python3
"""Fail CI when the S08-D10 traceability or final review regresses."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 8 review gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


traceability_path = "docs/sprints/sprint-8-traceability.md"
trace = read(traceability_path)
for identifier in (
    *(f"s08-r{index:02d}" for index in range(1, 13)),
    *(f"s08-t{index:02d}" for index in range(1, 13)),
    *(f"s08-d{index:02d}" for index in range(1, 11)),
):
    if identifier not in trace:
        fail(f"{traceability_path} does not trace {identifier.upper()}")

for phrase in (
    "fixed 2 km cells",
    "minimum 3 distinct accounts",
    "max 32 cells",
    "3.44 ms",
    "2.30 ms",
    "400 ms p95",
    "physical macbook",
    "not performed / not available",
    "no production map provider",
    "sprint 8 hardening run **#6**",
):
    if phrase not in trace:
        fail(f"{traceability_path} is missing {phrase!r}")

review_path = "docs/sprints/sprint-8-review.md"
review = read(review_path)
for phrase in (
    "approved upon merge of the s08-d10 review pull request",
    "does not authorize sprint 9 coding",
    "map is an awareness surface, not an authorization engine",
    "no production map provider or map dataset was selected",
    "approved current and incremental cost remains **$0 aws + $0 livekit cloud + $0 map/location provider per month**",
    "automated accessibility tests are regression evidence",
    "physical macbook",
    "issue #194 may close as completed",
    "tracker #195 may mark s08-d10 complete and close",
):
    if phrase not in review:
        fail(f"{review_path} is missing {phrase!r}")

physical = read("docs/sprints/sprint-8-d08-physical-compatibility.md")
for phrase in (
    "pass observed",
    "not performed",
    "exact macbook browser/version",
    "android physical-device evidence",
):
    if phrase not in physical:
        fail(f"Sprint 8 physical evidence is missing {phrase!r}")

hardening = read("docs/evidence/sprint-8/README.md")
for phrase in (
    "100 registered accounts",
    "25 presence viewers",
    "10 active publishers",
    "3.44 ms",
    "2.30 ms",
    "no production map provider selected",
):
    if phrase not in hardening:
        fail(f"Sprint 8 hardening evidence is missing {phrase!r}")

workflow = read(".github/workflows/sprint-8-hardening.yml")
if "python scripts/ci/check-sprint-8-review.py" not in workflow:
    fail("Sprint 8 hardening workflow does not enforce the final review gate")

print("Sprint 8 review gate: passed")
