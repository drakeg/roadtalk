#!/usr/bin/env python3
"""Fail CI when Sprint 9 planning loses a locked safety/provider/cost boundary."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 9 planning gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


def require(path: str, *phrases: str) -> None:
    content = read(path)
    for phrase in phrases:
        normalized = " ".join(phrase.lower().split())
        if normalized not in content:
            fail(f"{path} is missing {phrase!r}")


spec = "docs/sprints/sprint-9-notifications.md"
spec_text = read(spec)
for identifier in (
    *(f"s09-r{index:02d}" for index in range(1, 13)),
    *(f"s09-t{index:02d}" for index in range(1, 13)),
    *(f"s09-d{index:02d}" for index in range(1, 11)),
):
    if identifier not in spec_text:
        fail(f"{spec} does not define {identifier.upper()}")

require(
    spec,
    "notifications are an awareness/delivery surface, not an authorization engine",
    "roadtalk is not an emergency service",
    "delivery is not guaranteed",
    "contact local emergency services directly",
    "no automatic emergency detection",
    "disabled or deterministic fake delivery only",
    "$0 incremental recurring cost",
    "not authorized for activation",
    "no background location/audio",
    "100 accounts / 25 potential recipients / 10 alert publishers",
)

readiness = "docs/sprints/sprint-9-readiness.md"
require(
    readiness,
    "ready for product-owner review; not yet authorized for implementation",
    "sprint 8 is accepted by merged pr #219",
    "roadtalk is not an emergency service",
    "delivery is not guaranteed",
    "no external push provider is approved",
    "$0 incremental recurring cost",
    "sprint 10 campgrounds scope must not be pulled into sprint 9",
)

tracker = "https://github.com/drakeg/roadtalk/issues/229"
print(f"Sprint 9 planning gate: passed; tracker {tracker}")
