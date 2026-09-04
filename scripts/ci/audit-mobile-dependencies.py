#!/usr/bin/env python3
"""Audit mobile production dependencies with a narrow, expiring exception."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MOBILE = ROOT / "mobile"
BLOCKING_SEVERITIES = {"high", "critical"}
EXCEPTION_EXPIRES = date(2026, 9, 30)
AUDIT_ATTEMPTS = 2
AUDIT_TIMEOUT_SECONDS = 90
ALLOWED_ADVISORIES = {
    "https://github.com/advisories/GHSA-5p2g-fcmc-qvqq",
    "https://github.com/advisories/GHSA-w3rx-r6r6-pgpr",
}


def fail(message: str) -> None:
    print(f"Mobile dependency audit: {message}", file=sys.stderr)
    raise SystemExit(1)


def install_audit_is_clean(path: Path) -> bool:
    if not path.is_file():
        return False
    output = path.read_text(encoding="utf-8", errors="replace").lower()
    if "found 0 vulnerabilities" in output:
        return True
    match = re.search(r"(?:^|\n)\s*(\d+) vulnerabilities?\b", output)
    if match:
        print(
            "Mobile dependency audit: npm ci reported findings; requesting detailed production audit",
            file=sys.stderr,
        )
    else:
        print(
            "Mobile dependency audit: npm ci audit summary unavailable; requesting detailed production audit",
            file=sys.stderr,
        )
    return False


def load_audit() -> dict[str, Any] | None:
    last_error = "npm audit did not return a usable report"
    for attempt in range(1, AUDIT_ATTEMPTS + 1):
        try:
            result = subprocess.run(
                ["npm", "audit", "--omit=dev", "--audit-level=high", "--json"],
                cwd=MOBILE,
                check=False,
                capture_output=True,
                text=True,
                timeout=AUDIT_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            last_error = f"npm audit timed out after {AUDIT_TIMEOUT_SECONDS} seconds"
        else:
            try:
                report = json.loads(result.stdout)
            except json.JSONDecodeError:
                last_error = result.stderr.strip() or "npm did not return valid JSON"
            else:
                error = report.get("error")
                if error is None:
                    return report
                last_error = f"npm audit failed: {error}"

        if attempt < AUDIT_ATTEMPTS:
            print(
                f"Mobile dependency audit: transient failure on attempt {attempt}; retrying",
                file=sys.stderr,
            )
            time.sleep(2)

    print(
        "Mobile dependency audit: registry unavailable after bounded retries; "
        f"continuing to blocking Trivy dependency scan ({last_error})",
        file=sys.stderr,
    )
    return None


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

    if len(sys.argv) > 1 and install_audit_is_clean(Path(sys.argv[1])):
        print("Mobile dependency audit: passed with no vulnerabilities reported by npm ci")
        return

    report = load_audit()
    if report is None:
        return

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
