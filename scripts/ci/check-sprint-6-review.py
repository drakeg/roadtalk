#!/usr/bin/env python3
"""Fail CI when the S06-D09 traceability or review decision regresses."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 6 review gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


traceability = "docs/sprints/sprint-6-traceability.md"
trace = read(traceability)
for identifier in (
    *(f"s06-r{index:02d}" for index in range(1, 13)),
    *(f"s06-t{index:02d}" for index in range(1, 13)),
    *(f"s06-d{index:02d}" for index in range(1, 10)),
):
    if identifier not in trace:
        fail(f"{traceability} does not trace {identifier.upper()}")

for phrase in (
    "100 accounts/25 receivers/10 publishers",
    "eligible 35.52 ms",
    "cross-channel denied 3.64 ms",
    "selection/switch 11.97 ms",
    "invite verification 39.20 ms",
    "reconciliation 93.82 ms p95",
    "s01-e01 through s01-e03 remain field-test blockers",
):
    if phrase not in trace:
        fail(f"{traceability} is missing {phrase!r}")

review_path = "docs/sprints/sprint-6-review.md"
review = read(review_path)
for phrase in (
    "approved upon merge of the s06-d09 review",
    "does not authorize sprint 7 coding",
    "approved current and incremental cost: $0 aws + $0 livekit per month",
    "alerts, budgets, ci checks, and quotas are not automatic shutdown controls",
    "no live livekit room isolation/subscription/revocation",
    "s01-e01 through s01-e03 remain blockers for field testing",
    "issue #138 and tracker #139 may close",
    "issue #148",
):
    if phrase not in review:
        fail(f"{review_path} is missing {phrase!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-sprint-6-review.py" not in workflow:
    fail("CI does not enforce the Sprint 6 review gate")

print("Sprint 6 review gate: passed")
