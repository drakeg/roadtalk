#!/usr/bin/env python3
"""Audit mobile production dependencies with a narrow, expiring exception."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MOBILE = ROOT / "mobile"
BLOCKING_SEVERITIES = {"high", "critical"}
EXCEPTION_EXPIRES = date(2026, 9, 30)
ALLOWED_ADVISORIES = {
    "https://github.com/advisories/GHSA-5p2g-fcmc-qvqq",
    "https://github.com/advisories/GHSA-w3rx-r6r6-pgpr",
}


def fail(message: str) -> None:
    print(f"Mobile dependency audit: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_audit() -> dict[str, Any]:
    result = subprocess.run(
        ["npm", "audit", "--omit=dev", "--audit-level=high", "--json"],
        cwd=MOBILE,
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        detail = result.stderr.strip() or "npm did not return valid JSON"
        fail(f"could not read npm audit results: {detail}")
    if "error" in report:
        fail(f"npm audit failed: {report['error']}")
    return report


def is_allowlisted(
    package: str,
    vulnerabilities: dict[str, Any],
) -> bool:
    pending = [package]
    visited: set[str] = set()
    advisories: set[str] = set()

    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        finding = vulnerabilities.get(current)
        if not isinstance(finding, dict):
            return False

        for cause in finding.get("via", []):
            if isinstance(cause, str):
                pending.append(cause)
            elif isinstance(cause, dict) and cause.get("severity") in BLOCKING_SEVERITIES:
                url = cause.get("url")
                if not isinstance(url, str):
                    return False
                advisories.add(url)

    return bool(advisories) and advisories <= ALLOWED_ADVISORIES


def main() -> None:
    if date.today() > EXCEPTION_EXPIRES:
        fail(
            "the image-size advisory exception expired on "
            f"{EXCEPTION_EXPIRES.isoformat()}"
        )

    report = load_audit()
    vulnerabilities = report.get("vulnerabilities")
    if not isinstance(vulnerabilities, dict):
        fail("npm audit results do not contain a vulnerabilities object")

    blocking = sorted(
        package
        for package, finding in vulnerabilities.items()
        if isinstance(finding, dict)
        and finding.get("severity") in BLOCKING_SEVERITIES
        and not is_allowlisted(package, vulnerabilities)
    )
    if blocking:
        fail("unapproved high/critical findings: " + ", ".join(blocking))

    excepted = sorted(
        package
        for package, finding in vulnerabilities.items()
        if isinstance(finding, dict)
        and finding.get("severity") in BLOCKING_SEVERITIES
        and is_allowlisted(package, vulnerabilities)
    )
    if excepted:
        print(
            "Mobile dependency audit: passed with the approved image-size "
            f"exception through {EXCEPTION_EXPIRES.isoformat()} "
            f"({', '.join(excepted)})"
        )
    else:
        print("Mobile dependency audit: passed with no high/critical findings")


if __name__ == "__main__":
    main()
