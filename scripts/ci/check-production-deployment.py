#!/usr/bin/env python3
"""Validate Sprint 15 D06 deployment/rollback automation boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "deployment-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    auth = data["authorization"]
    require(auth["deployment_authorized"] is False, "D06 must not authorize production deployment")
    require(auth["manual_approval_required"] is True, "manual approval required")
    require(auth["pull_request_deploy_allowed"] is False, "PR deploys are prohibited")
    require(auth["automatic_real_user_rollout_allowed"] is False, "automatic real-user rollout is prohibited")

    artifact = data["artifact"]
    require(artifact["immutable_digest_required"] is True, "immutable digest required")
    require(artifact["mutable_tag_allowed"] is False, "mutable tags prohibited")
    require(artifact["provenance_required"] is True, "provenance required")
    require(artifact["sbom_required"] is True, "SBOM required")
    require(artifact["rollback_artifact_required"] is True, "rollback artifact required")

    plan = data["plan"]
    require(plan["exact_plan_required"] is True, "exact plan required")
    require(plan["plan_apply_identity_match_required"] is True, "plan/apply identity binding required")
    require(1 <= plan["plan_expiry_minutes_max"] <= 60, "plan must expire within 60 minutes")
    require(plan["drift_check_required_before_apply"] is True, "drift check required")

    migration = data["migration"]
    require(migration["preflight_required"] is True, "migration preflight required")
    require(migration["backward_compatibility_required"] is True, "backward compatibility required")
    require(migration["irreversible_change_requires_separate_approval"] is True, "irreversible changes require separate approval")
    require(migration["irreversible_change_blocks_automatic_rollback"] is True, "irreversible migrations block automatic rollback")
    require(migration["destructive_change_default_allowed"] is False, "destructive changes must default deny")

    deploy = data["deployment"]
    require(deploy["pre_health_gate_required"] is True, "pre-health gate required")
    require(deploy["post_health_gate_required"] is True, "post-health gate required")
    require(5 <= deploy["minimum_observation_minutes"] <= 60, "observation must be 5-60 minutes")
    require(deploy["single_batch_full_fleet_replacement_allowed"] is False, "full-fleet one-shot replacement prohibited")
    require(deploy["failed_health_requires_rollback_or_halt"] is True, "failed health must halt or rollback")

    rollback = data["rollback"]
    require(rollback["named_target_required"] is True, "named rollback target required")
    require(rollback["exact_digest_required"] is True, "rollback requires exact digest")
    require(rollback["database_state_check_required"] is True, "database state check required")
    require(rollback["manual_approval_required"] is True, "rollback approval required")
    require(rollback["emergency_disable_required"] is True, "emergency disable required")
    require(rollback["rollback_to_mutable_tag_allowed"] is False, "mutable rollback target prohibited")

    evidence = data["evidence"]
    require(evidence["dry_run_validation_required"] is True, "dry-run validation required")
    for key in ("live_production_deploy_performed", "live_production_rollback_performed", "real_user_traffic_shifted"):
        require(evidence[key] is False, f"D06 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("deployment authorization", ("authorization", "deployment_authorized"), True),
        ("PR deploy", ("authorization", "pull_request_deploy_allowed"), True),
        ("mutable image", ("artifact", "mutable_tag_allowed"), True),
        ("stale plan", ("plan", "plan_expiry_minutes_max"), 240),
        ("no drift check", ("plan", "drift_check_required_before_apply"), False),
        ("destructive migration", ("migration", "destructive_change_default_allowed"), True),
        ("one-shot fleet replacement", ("deployment", "single_batch_full_fleet_replacement_allowed"), True),
        ("missing health rollback", ("deployment", "failed_health_requires_rollback_or_halt"), False),
        ("mutable rollback target", ("rollback", "rollback_to_mutable_tag_allowed"), True),
        ("false live deploy evidence", ("evidence", "live_production_deploy_performed"), True),
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
        raise SystemExit(f"negative deployment test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 15 production deployment contract: valid")


if __name__ == "__main__":
    main()
