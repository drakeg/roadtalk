#!/usr/bin/env python3
"""Fail CI when proposed Sprint 5 planning loses an approved safety boundary."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 5 planning gate: {message}", file=sys.stderr)
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


specification = "docs/sprints/sprint-5-proximity.md"
specification_text = read(specification)
for identifier in (
    *(f"s05-r{index:02d}" for index in range(1, 13)),
    *(f"s05-t{index:02d}" for index in range(1, 13)),
    *(f"s05-d{index:02d}" for index in range(1, 10)),
):
    if identifier not in specification_text:
        fail(f"{specification} does not define {identifier.upper()}")

require(
    specification,
    "proposed — awaiting product-owner approval",
    "automatic subscription disabled",
    "post /api/v1/ptt/grants/{transmit_grant_id}/publication",
    "no eligible-recipient list is returned",
    "100 accounts, 25 receivers, and 10 publishers",
    "proximity/grant p95 ≤400 ms",
    "add no aws resource, redis, rds, queue, worker, scheduler",
    "current and incremental recurring cost",
    "**$0**",
    "always-on aws or paid livekit",
    "**prohibited**",
)

readiness = "docs/sprints/sprint-5-readiness.md"
require(
    readiness,
    "status: not ready — awaiting product-owner approval",
    "current and incremental cost: **$0 aws + $0 livekit per month**",
    "coding remains blocked until explicit approval",
    "auto-subscription is on by default",
    "updateSubscriptions".lower(),
    "no recipient-membership persistence is needed",
    "s01-e01 through s01-e03 continue to block field tests",
    "physical media nfrs",
    "terraform | disabled; zero resources",
)

review = read("docs/sprints/sprint-4-review.md")
if "status: approved — merged pr #108" not in review:
    fail("Sprint 4 review is not recorded as approved")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-sprint-5-planning.py" not in workflow:
    fail("CI does not enforce the Sprint 5 planning gate")

print("Sprint 5 planning gate: passed")
