#!/usr/bin/env python3
"""Fail CI when Sprint 14 Premium planning boundaries regress."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 14 planning gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


spec = read("docs/sprints/sprint-14-premium.md")
readiness = read("docs/sprints/sprint-14-readiness.md")

for identifier in (
    *(f"s14-r{index:02d}" for index in range(1, 13)),
    *(f"s14-t{index:02d}" for index in range(1, 13)),
):
    if identifier not in spec:
        fail(f"Sprint 14 specification does not define {identifier.upper()}")

for issue in (355, 356, 346, 347, 348, 349, 350, 351, 352, 353, 354):
    if f"#{issue}" not in spec and f"#{issue}" not in readiness:
        fail(f"Sprint 14 planning does not reference issue #{issue}")

for phrase in (
    "incremental recurring implementation cost is $0",
    "no real-money/provider/store activation is authorized by d01",
    "does not authorize that activation",
    "client may self-assert premium entitlement",
    "tax collection/remittance",
    "sprint 15 production",
):
    if phrase not in readiness:
        fail(f"Sprint 14 readiness is missing required boundary {phrase!r}")

for forbidden in (
    "stripe secret key",
    "stripe_secret_key",
    "apple shared secret",
    "google service account",
    "live payment provider is enabled",
):
    if forbidden in spec or forbidden in readiness:
        fail(f"Sprint 14 planning contains live-provider material {forbidden!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-sprint-14-planning.py" not in workflow:
    fail("CI does not enforce the Sprint 14 planning gate")

print("Sprint 14 planning gate: passed")
