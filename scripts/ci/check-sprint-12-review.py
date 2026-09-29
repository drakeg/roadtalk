#!/usr/bin/env python3
"""Fail CI when Sprint 12 final traceability or acceptance boundaries regress."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 12 review gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


review_path = "docs/evidence/sprint-12-d10-final-review.md"
review = read(review_path)

for identifier in (
    *(f"s12-r{index:02d}" for index in range(1, 13)),
    *(f"s12-t{index:02d}" for index in range(1, 13)),
):
    if identifier not in review:
        fail(f"{review_path} does not trace {identifier.upper()}")

for issue in range(296, 306):
    if f"#{issue}" not in review:
        fail(f"{review_path} does not reference Sprint 12 issue #{issue}")

for pr in range(307, 316):
    if f"pr #{pr}" not in review:
        fail(f"{review_path} does not reference merged Sprint 12 PR #{pr}")

for phrase in (
    "incremental recurring implementation cost remains $0",
    "moderation state is restrictive only",
    "physical-device moderation behavior",
    "production/public-beta operation",
    "not performed",
    "does not authorize sprint 13 implementation",
    "sprint 13 requires separate planning/readiness approval",
):
    if phrase not in review:
        fail(f"{review_path} is missing required acceptance boundary {phrase!r}")

workflow = read(".github/workflows/ci.yml")
for command in (
    "python scripts/ci/check-moderation-compatibility.py",
    "python scripts/ci/check-sprint-12-review.py",
):
    if command not in workflow:
        fail(f"CI does not enforce {command!r}")

print("Sprint 12 review gate: passed")
