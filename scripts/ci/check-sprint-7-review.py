#!/usr/bin/env python3
"""Fail CI when the S07-D09 traceability or review decision regresses."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 7 review gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


traceability_path = "docs/sprints/sprint-7-traceability.md"
trace = read(traceability_path)
for identifier in (
    *(f"s07-r{index:02d}" for index in range(1, 13)),
    *(f"s07-t{index:02d}" for index in range(1, 13)),
    *(f"s07-d{index:02d}" for index in range(1, 10)),
):
    if identifier not in trace:
        fail(f"{traceability_path} does not trace {identifier.upper()}")

for phrase in (
    "100 accounts/25 receivers/10 publishers",
    "nearby 40.71 ms",
    "same-road 24.03 ms",
    "zero-recipient denial 18.97 ms",
    "reconciliation 160.94 ms",
    "s01-e01 through s01-e03 remain relevant",
    "real-road matching quality",
    "cross-browser/physical-system microphone/speaker",
):
    if phrase not in trace:
        fail(f"{traceability_path} is missing {phrase!r}")

review_path = "docs/sprints/sprint-7-review.md"
review = read(review_path)
for phrase in (
    "approved upon merge of the s07-d09 review pull request",
    "does not authorize sprint 8 coding",
    "approved current and incremental cost: **$0 aws + $0 livekit cloud + $0 routing provider per month**",
    "alerts, budgets, ci checks, quotas and cost ceilings are **not automatic shutdown controls**",
    "real routing provider remains hard-disabled",
    "odbl attribution",
    "physical cross-system microphone/location exception",
    "issue #172 may close as completed",
    "tracker #173 may mark s07-d09 complete and close",
):
    if phrase not in review:
        fail(f"{review_path} is missing {phrase!r}")

hardening = read("docs/evidence/sprint-7/README.md")
for phrase in (
    "40.71 ms",
    "24.03 ms",
    "18.97 ms",
    "160.94 ms",
    "live-provider, physical-device, and field status: **not performed**",
):
    if phrase not in hardening:
        fail(f"Sprint 7 evidence is missing {phrase!r}")

workflow = read(".github/workflows/sprint-7-hardening.yml")
if "python scripts/ci/check-sprint-7-review.py" not in workflow:
    fail("Sprint 7 hardening workflow does not enforce the final review gate")

print("Sprint 7 review gate: passed")
