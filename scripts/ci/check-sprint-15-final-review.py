#!/usr/bin/env python3
"""Validate Sprint 15 D10 final production-readiness traceability."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_CONTRACTS = [
    "production-contract.json",
    "identity-contract.json",
    "observability-contract.json",
    "backup-contract.json",
    "deployment-contract.json",
    "resilience-contract.json",
    "security-privacy-contract.json",
    "governance-contract.json",
]

REQUIRED_EVIDENCE = [
    "sprint-15-d02-production-contract.md",
    "sprint-15-d03-production-identity.md",
    "sprint-15-d04-production-observability.md",
    "sprint-15-d05-production-backup.md",
    "sprint-15-d06-production-deployment.md",
    "sprint-15-d07-production-resilience.md",
    "sprint-15-d08-production-security-privacy.md",
    "sprint-15-d09-production-governance.md",
    "sprint-15-d10-final-production-readiness.md",
]

REQUIRED_CHECKERS = [
    "check-production-contract.py",
    "check-production-identity.py",
    "check-production-observability.py",
    "check-production-backup.py",
    "check-production-deployment.py",
    "check-production-resilience.py",
    "check-production-security-privacy.py",
    "check-production-governance.py",
]

LIVE_EXCEPTION_PHRASES = [
    "live production",
    "public-beta",
    "load",
    "failover",
    "disaster-recovery",
    "billing",
    "provider",
    "recurring production spend",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    prod = ROOT / "infrastructure" / "environments" / "production"
    evidence = ROOT / "docs" / "evidence"
    ci = ROOT / "scripts" / "ci"
    final_review = evidence / "sprint-15-d10-final-production-readiness.md"

    for name in REQUIRED_CONTRACTS:
        require((prod / name).is_file(), f"missing Sprint 15 contract: {name}")
    for name in REQUIRED_EVIDENCE:
        require((evidence / name).is_file(), f"missing Sprint 15 evidence: {name}")
    for name in REQUIRED_CHECKERS:
        require((ci / name).is_file(), f"missing Sprint 15 checker: {name}")

    text = final_review.read_text()
    for requirement in [f"S15-R{i:02d}" for i in range(1, 13)]:
        require(requirement in text, f"final review missing {requirement}")
    for test in [f"S15-T{i:02d}" for i in range(1, 13)]:
        require(test in text, f"final review missing {test}")
    for pr in ("#456", "#459", "#460", "#461", "#462", "#463", "#464", "#465", "#466"):
        require(pr in text, f"final review missing delivery PR {pr}")
    for phrase in LIVE_EXCEPTION_PHRASES:
        require(phrase.lower() in text.lower(), f"final review missing live-evidence exception: {phrase}")

    prohibited_claims = [
        "production launch authorized",
        "public beta authorized",
        "live load test passed",
        "disaster recovery proven",
        "billing validated",
    ]
    lower = text.lower()
    for claim in prohibited_claims:
        require(claim not in lower, f"final review contains prohibited overclaim: {claim}")

    print("Sprint 15 final production-readiness traceability: valid")


if __name__ == "__main__":
    main()
