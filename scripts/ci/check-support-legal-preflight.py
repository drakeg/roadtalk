#!/usr/bin/env python3
"""Validate Sprint 16 D08 support/privacy/security/legal launch obligations."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "support-legal-preflight-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    gate = data["launch_gate"]
    for key in (
        "fail_closed",
        "unresolved_obligations_block_launch",
        "security_privacy_gate_required",
        "support_gate_required",
        "retention_deletion_gate_required",
        "terms_privacy_content_gate_required",
        "legal_review_gate_required",
    ):
        require(gate[key] is True, f"{key} must be required")

    support = data["support"]
    for key in (
        "operational_owner_required",
        "incident_communications_owner_required",
        "support_contact_path_required",
        "severity_and_escalation_required",
        "coverage_model_required",
    ):
        require(support[key] is True, f"{key} must be required")
    require((ROOT / support["runbook"]).is_file(), "support runbook must exist")

    sec = data["security_privacy"]
    for key in (
        "production_security_privacy_contract_required",
        "high_or_critical_findings_block_launch",
        "privacy_regressions_block_launch",
        "unsafe_tracking_blocks_launch",
        "exceptions_must_be_owned_and_expiring",
    ):
        require(sec[key] is True, f"{key} must be required")
    require(sec["unsupported_compliance_claims_allowed"] is False, "unsupported compliance claims prohibited")

    retention = data["retention_deletion"]
    for key in (
        "inventory_required",
        "retention_schedule_required",
        "account_deletion_behavior_required",
        "backup_deletion_delay_disclosure_required",
        "technical_inventory_documented",
        "retention_schedule_drafted",
        "deletion_behavior_drafted",
    ):
        require(retention[key] is True, f"{key} must be required")
    require((ROOT / retention["document"]).is_file(), "retention/deletion document must exist")

    content = data["terms_privacy_content"]
    require(content["terms_content_required"] is True, "terms content required")
    require(content["privacy_notice_content_required"] is True, "privacy notice content required")
    require((ROOT / content["terms_document"]).is_file(), "terms draft must exist")
    require((ROOT / content["privacy_document"]).is_file(), "privacy notice draft must exist")
    require(content["legal_counsel_review_claimed"] is False, "must not claim legal counsel review")

    unresolved = data["unresolved_obligations"]
    require(isinstance(unresolved, list) and unresolved, "unresolved obligations must be recorded while readiness is false")

    blockers = [
        not support["operational_owner_assigned"],
        not support["incident_communications_owner_assigned"],
        not support["support_contact_published"],
        not support["coverage_model_approved"],
        not retention["final_policy_review_complete"],
        not content["terms_final_approved"],
        not content["privacy_notice_final_approved"],
        bool(unresolved),
    ]
    if any(blockers):
        require(data["public_beta_ready"] is False, "public beta must remain blocked while D08 obligations are unresolved")

    evidence = data["evidence"]
    require(evidence["deterministic_preflight_validated"] is True, "deterministic D08 preflight required")
    for key in (
        "live_support_exercise_performed",
        "live_privacy_audit_performed",
        "legal_counsel_review_performed",
        "public_beta_launched",
    ):
        require(evidence[key] is False, f"D08 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("fail-open gate", ("launch_gate", "fail_closed"), False),
        ("high findings allowed", ("security_privacy", "high_or_critical_findings_block_launch"), False),
        ("privacy regression allowed", ("security_privacy", "privacy_regressions_block_launch"), False),
        ("unsupported compliance claim", ("security_privacy", "unsupported_compliance_claims_allowed"), True),
        ("missing retention schedule", ("retention_deletion", "retention_schedule_required"), False),
        ("missing deletion behavior", ("retention_deletion", "account_deletion_behavior_required"), False),
        ("terms not required", ("terms_privacy_content", "terms_content_required"), False),
        ("privacy notice not required", ("terms_privacy_content", "privacy_notice_content_required"), False),
        ("false counsel claim", ("terms_privacy_content", "legal_counsel_review_claimed"), True),
        ("false support exercise", ("evidence", "live_support_exercise_performed"), True),
        ("false legal review evidence", ("evidence", "legal_counsel_review_performed"), True),
        ("launch while blocked", ("public_beta_ready",), True),
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
        raise SystemExit(f"negative D08 preflight test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 16 support/privacy/security/legal preflight: valid and launch blocked")


if __name__ == "__main__":
    main()
