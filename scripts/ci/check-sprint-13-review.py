#!/usr/bin/env python3
"""Fail CI when Sprint 13 final traceability or acceptance boundaries regress."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 13 review gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


review_path = "docs/evidence/sprint-13-d10-final-review.md"
review = read(review_path)

for identifier in (
    *(f"s13-r{index:02d}" for index in range(1, 13)),
    *(f"s13-t{index:02d}" for index in range(1, 13)),
):
    if identifier not in review:
        fail(f"{review_path} does not trace {identifier.upper()}")

for issue in (326, 317, 318, 319, 320, 321, 322, 323, 324, 325):
    if f"#{issue}" not in review:
        fail(f"{review_path} does not reference Sprint 13 issue #{issue}")

for pr in (328, 329, 330, 331, 332, 333, 334, 336, 340):
    if f"pr #{pr}" not in review:
        fail(f"{review_path} does not reference merged Sprint 13 PR #{pr}")

for phrase in (
    "incremental recurring implementation cost remains $0",
    "no external ai or speech provider is authorized or activated",
    "physical-device microphone/transcription behavior",
    "production/public-beta operation",
    "live-provider",
    "not performed",
    "does not authorize sprint 14 premium implementation",
    "sprint 14 requires separate planning/readiness approval",
):
    if phrase not in review:
        fail(f"{review_path} is missing required acceptance boundary {phrase!r}")

workflow = read(".github/workflows/ci.yml")
for command in (
    "python scripts/ci/check-sprint-13-ai-hardening.py",
    "python scripts/ci/check-sprint-13-review.py",
):
    if command not in workflow:
        fail(f"CI does not enforce {command!r}")

print("Sprint 13 review gate: passed")
