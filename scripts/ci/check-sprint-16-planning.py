#!/usr/bin/env python3
"""Validate the Sprint 16 public-beta readiness planning baseline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs" / "sprints" / "sprint-16-public-beta.md"
READY = ROOT / "docs" / "sprints" / "sprint-16-readiness.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    require(SPEC.is_file(), "missing Sprint 16 specification")
    require(READY.is_file(), "missing Sprint 16 readiness document")

    spec = SPEC.read_text()
    ready = READY.read_text()
    combined = spec + "\n" + ready

    for requirement in [f"S16-R{i:02d}" for i in range(1, 13)]:
        require(requirement in spec, f"missing {requirement}")
    for test in [f"S16-T{i:02d}" for i in range(1, 13)]:
        require(test in spec, f"missing {test}")
    for issue in [f"#{i}" for i in range(476, 487)]:
        require(issue in combined, f"missing Sprint 16 issue reference {issue}")

    required_boundaries = [
        "defaults false",
        "does not itself authorize",
        "recurring spend",
        "DNS cutover",
        "real-money",
        "live evidence",
        "blocked until",
    ]
    lower = combined.lower()
    for phrase in required_boundaries:
        require(phrase.lower() in lower, f"missing planning boundary: {phrase}")

    prohibited = [
        "public beta authorized",
        "production traffic authorized",
        "recurring spend authorized",
        "dns cutover authorized",
    ]
    for phrase in prohibited:
        require(phrase not in lower, f"planning overclaim: {phrase}")

    print("Sprint 16 planning gate: passed")


if __name__ == "__main__":
    main()
