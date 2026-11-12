#!/usr/bin/env python3
"""Validate Sprint 15 D09 production cost/support/legal boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "governance-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    cost = data["cost"]
    require(cost["recurring_spend_authorized"] is False, "D09 must not authorize recurring spend")
    for key in (
        "cost_model_required_before_launch",
        "monthly_budget_owner_required",
        "provider_costs_separately_approved",
        "cost_alerts_required",
        "cost_anomaly_review_required",
    ):
        require(cost[key] is True, f"{key} must be required")
    require(cost["unbounded_usage_pricing_allowed"] is False, "unbounded usage pricing is prohibited")

    support = data["support"]
    for key in (
        "operational_owner_required",
        "incident_owner_required",
        "support_contact_path_required",
        "severity_model_required",
        "escalation_path_required",
        "runbook_index_required",
    ):
        require(support[key] is True, f"{key} must be required")
    require(support["business_hours_only_support_assumption_allowed"] is False, "production support cannot assume business-hours-only availability")

    legal = data["legal_privacy"]
    for key in (
        "privacy_policy_review_required",
        "terms_review_required",
        "data_retention_review_required",
        "data_deletion_review_required",
        "provider_terms_review_required_before_activation",
        "app_store_policy_review_required_before_store_release",
        "payment_tax_obligations_review_required_before_real_money",
    ):
        require(legal[key] is True, f"{key} must be required")
    require(legal["unsupported_compliance_claims_allowed"] is False, "unsupported compliance claims prohibited")

    providers = data["providers"]
    require(providers["premium_provider_default"] == "disabled", "Premium provider must default disabled")
    require(providers["payment_provider_default"] == "disabled", "payment provider must default disabled")
    require(providers["store_provider_default"] == "disabled", "store provider must default disabled")
    require(providers["provider_credentials_present_before_approval_allowed"] is False, "provider credentials must not predate approval")
    require(providers["provider_activation_requires_named_approval"] is True, "provider activation requires named approval")

    rollback = data["rollback_disable"]
    for key in (
        "named_rollback_target_required",
        "emergency_disable_required",
        "provider_kill_switch_required",
        "public_beta_disable_path_required",
        "dns_rollback_plan_required",
        "irreversible_change_requires_named_exception",
    ):
        require(rollback[key] is True, f"{key} must be required")

    exc = data["exceptions"]
    for key in ("owner_required", "reason_required", "expiry_required", "impact_required", "rollback_or_mitigation_required"):
        require(exc[key] is True, f"{key} must be required")
    require(exc["permanent_exception_allowed"] is False, "permanent exceptions prohibited")

    evidence = data["evidence"]
    require(evidence["deterministic_review_contract_validated"] is True, "deterministic review validation required")
    for key in (
        "live_billing_validated",
        "live_support_exercise_performed",
        "legal_counsel_review_claimed",
        "real_provider_activation_performed",
    ):
        require(evidence[key] is False, f"D09 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("recurring spend authorized", ("cost", "recurring_spend_authorized"), True),
        ("unbounded provider pricing", ("cost", "unbounded_usage_pricing_allowed"), True),
        ("no support owner", ("support", "operational_owner_required"), False),
        ("business-hours-only support", ("support", "business_hours_only_support_assumption_allowed"), True),
        ("skip provider terms", ("legal_privacy", "provider_terms_review_required_before_activation"), False),
        ("unsupported compliance claim", ("legal_privacy", "unsupported_compliance_claims_allowed"), True),
        ("payment provider enabled", ("providers", "payment_provider_default"), "live"),
        ("credentials before approval", ("providers", "provider_credentials_present_before_approval_allowed"), True),
        ("missing provider kill switch", ("rollback_disable", "provider_kill_switch_required"), False),
        ("permanent exception", ("exceptions", "permanent_exception_allowed"), True),
        ("false live billing evidence", ("evidence", "live_billing_validated"), True),
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
        raise SystemExit(f"negative governance test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 15 production governance contract: valid")


if __name__ == "__main__":
    main()
