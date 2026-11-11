#!/usr/bin/env python3
"""Validate Sprint 15 D08 production security/privacy release gates."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "security-privacy-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    gate = data["release_gate"]
    require(gate["fail_closed"] is True, "release gate must fail closed")
    require(gate["unresolved_high_or_critical_findings_allowed"] is False, "high/critical findings must block release")
    require(gate["unapproved_security_exception_allowed"] is False, "unapproved security exceptions prohibited")
    require(gate["unapproved_privacy_exception_allowed"] is False, "unapproved privacy exceptions prohibited")
    require(gate["manual_release_approval_required"] is True, "manual release approval required")

    scans = data["security_scans"]
    for key in (
        "python_dependency_audit_required",
        "mobile_dependency_audit_required",
        "container_scan_required",
        "filesystem_secret_scan_required",
        "iac_misconfiguration_scan_required",
        "high_severity_blocks_release",
        "critical_severity_blocks_release",
    ):
        require(scans[key] is True, f"{key} must be required")
    require(scans["ignore_unfixed_allowed_only_when_documented"] is True, "unfixed exceptions must be documented")

    creds = data["credentials"]
    require(creds["repository_secret_leak_allowed"] is False, "repository secret leaks prohibited")
    require(creds["ci_log_secret_leak_allowed"] is False, "CI secret leaks prohibited")
    require(creds["static_cloud_credentials_allowed"] is False, "static cloud credentials prohibited")
    require(creds["production_oidc_required"] is True, "production OIDC required")
    require(creds["secret_rotation_policy_required"] is True, "secret rotation policy required")

    auth = data["authorization"]
    require(auth["least_privilege_required"] is True, "least privilege required")
    require(auth["admin_access_default_allowed"] is False, "admin access must default deny")
    require(auth["pull_request_production_deploy_allowed"] is False, "PR production deploy prohibited")
    require(auth["cross_environment_secret_access_allowed"] is False, "cross-environment secret access prohibited")
    require(auth["shared_human_identity_allowed"] is False, "shared human identity prohibited")

    privacy = data["privacy"]
    for key in (
        "precise_location_in_logs_allowed",
        "raw_authorization_headers_in_logs_allowed",
        "raw_cookie_headers_in_logs_allowed",
        "payment_instrument_storage_allowed",
        "unrelated_user_payload_logging_allowed",
        "user_identifier_metric_labels_allowed",
    ):
        require(privacy[key] is False, f"{key} must remain false")
    require(privacy["privacy_regression_checks_required"] is True, "privacy regression checks required")

    unsafe = data["unsafe_configuration"]
    require(unsafe["public_database_allowed"] is False, "public database prohibited")
    require(unsafe["public_cache_allowed"] is False, "public cache prohibited")
    require(unsafe["tls_required"] is True, "TLS required")
    require(unsafe["minimum_tls_version"] in ("1.2", "1.3"), "minimum TLS must be 1.2 or newer")
    require(unsafe["mutable_release_artifact_allowed"] is False, "mutable release artifact prohibited")
    require(unsafe["plaintext_secret_configuration_allowed"] is False, "plaintext secret configuration prohibited")

    exc = data["exceptions"]
    for key in ("owner_required", "reason_required", "expiry_required", "risk_acceptance_required", "compensating_control_required"):
        require(exc[key] is True, f"{key} must be required")
    require(exc["permanent_exception_allowed"] is False, "permanent exceptions prohibited")

    evidence = data["evidence"]
    require(evidence["deterministic_release_gate_validated"] is True, "deterministic release gate validation required")
    for key in (
        "live_penetration_test_performed",
        "live_production_security_test_performed",
        "live_privacy_audit_performed",
    ):
        require(evidence[key] is False, f"D08 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("fail-open release gate", ("release_gate", "fail_closed"), False),
        ("high finding allowed", ("release_gate", "unresolved_high_or_critical_findings_allowed"), True),
        ("container scan missing", ("security_scans", "container_scan_required"), False),
        ("static cloud credentials", ("credentials", "static_cloud_credentials_allowed"), True),
        ("PR production deploy", ("authorization", "pull_request_production_deploy_allowed"), True),
        ("precise location logging", ("privacy", "precise_location_in_logs_allowed"), True),
        ("payment instrument storage", ("privacy", "payment_instrument_storage_allowed"), True),
        ("public database", ("unsafe_configuration", "public_database_allowed"), True),
        ("TLS 1.1", ("unsafe_configuration", "minimum_tls_version"), "1.1"),
        ("permanent exception", ("exceptions", "permanent_exception_allowed"), True),
        ("false live security evidence", ("evidence", "live_penetration_test_performed"), True),
    ]
    for label, path, value in cases:
        candidate = copy.deepcopy(data)
        target: Any = candidate
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        try:
            validate(candidate)
        except ValueError:
            continue
        raise SystemExit(f"negative security/privacy test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 15 production security/privacy contract: valid")


if __name__ == "__main__":
    main()
