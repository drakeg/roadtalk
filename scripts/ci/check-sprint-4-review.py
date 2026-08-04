#!/usr/bin/env python3
"""Fail CI when the final Sprint 4 traceability or review boundary drifts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 4 review gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


def require(path: str, *phrases: str) -> None:
    content = read(path)
    for phrase in phrases:
        if " ".join(phrase.lower().split()) not in content:
            fail(f"{path} is missing {phrase!r}")


traceability = "docs/sprints/sprint-4-traceability.md"
for identifier in (
    *(f"s04-r{index:02d}" for index in range(1, 13)),
    *(f"s04-t{index:02d}" for index in range(1, 13)),
    *(f"s04-d{index:02d}" for index in range(1, 10)),
):
    if identifier not in read(traceability):
        fail(f"{traceability} does not trace {identifier.upper()}")

require(
    traceability,
    "status: complete — product-owner approved by merged pr #108",
    "current and incremental recurring cost is **$0/month**",
    "100 synthetic accounts, 25 connected receivers, 10 publishers",
    "synthetic grant p95 does not prove media latency or physical capacity",
    "s01-e01 through s01-e03 remain open",
)

review = "docs/sprints/sprint-4-review.md"
require(
    review,
    "status: approved — merged pr #108 on 2026-08-04",
    "product-owner decision became **approved**",
    "does **not** create or enable aws or livekit",
    "approved current and incremental cost: $0 aws + $0 livekit per month",
    "always-on aws, paid livekit",
    "the synthetic scale test measures local grant-service/database behavior",
    "sprint 5 planning",
)

evidence = "docs/evidence/sprint-4/README.md"
require(
    evidence,
    "d09 ci and measured grant p95: [run 30872939267]",
    "95 eligible requests at 6.57 ms p95",
    "10 busy denials at 3.97 ms p95",
    "review approval did not activate a provider or cloud environment",
)

scale_test = "backend/tests/test_ptt_scale.py"
scale_content = read(scale_test)
for expected in ("range(100)", "range(25)", "range(10)", "<= 250"):
    if expected not in scale_content:
        fail(f"{scale_test} is missing scale control {expected!r}")
if not re.search(r"eligible_p95_ms\s*<=\s*250", scale_content):
    fail(f"{scale_test} does not enforce the eligible p95 target")
if not re.search(r"denied_p95_ms\s*<=\s*250", scale_content):
    fail(f"{scale_test} does not enforce the denied p95 target")

workflow = read(".github/workflows/ci.yml")
for command in (
    "python scripts/ci/check-sprint-4-review.py",
    "pytest -q -s tests/test_ptt_scale.py",
):
    if command not in workflow:
        fail(f"CI is missing {command!r}")

print("Sprint 4 review gate: passed")
