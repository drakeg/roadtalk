#!/usr/bin/env python3
"""Validate Sprint 15 D05 production backup/restore boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "backup-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    scope = data["scope"]
    require(scope["primary_database_required"] is True, "primary database backup is required")
    require(scope["configuration_backup_required"] is True, "configuration backup is required")
    require(scope["terraform_state_backup_required"] is True, "Terraform state backup is required")
    require(scope["secret_values_in_backup_allowed"] is False, "secret values must not be copied into generic backups")

    protection = data["protection"]
    for key in (
        "encryption_at_rest_required",
        "encryption_in_transit_required",
        "cross_failure_domain_copy_required",
        "versioning_or_immutable_recovery_points_required",
        "backup_delete_protection_required",
    ):
        require(protection[key] is True, f"{key} must be required")
    require(
        protection["production_runtime_identity_can_delete_all_backups"] is False,
        "production runtime identity must not be able to delete all backups",
    )

    retention = data["retention"]
    require(retention["daily_recovery_points_min"] >= 7, "at least seven daily recovery points are required")
    require(retention["weekly_recovery_points_min"] >= 4, "at least four weekly recovery points are required")
    require(retention["monthly_recovery_points_min"] >= 3, "at least three monthly recovery points are required")
    require(30 <= retention["retention_days_min"] <= retention["retention_days_max"], "retention bounds are invalid")
    require(retention["retention_days_max"] <= 365, "default production retention must stay within one year absent separate approval")

    objectives = data["recovery_objectives"]
    require(1 <= objectives["rpo_minutes_max"] <= 60, "RPO target must be 60 minutes or less")
    require(1 <= objectives["rto_minutes_max"] <= 240, "RTO target must be four hours or less")
    require(
        objectives["objectives_require_live_validation_before_launch"] is True,
        "RPO/RTO targets require live validation before launch approval",
    )

    restore = data["restore_validation"]
    for key in (
        "automated_integrity_check_required",
        "restore_to_isolated_target_required",
        "schema_validation_required",
        "application_smoke_validation_required",
        "evidence_record_required",
    ):
        require(restore[key] is True, f"{key} must be required")
    require(restore["production_overwrite_during_test_allowed"] is False, "restore tests must never overwrite production")
    require(1 <= restore["restore_test_interval_days_max"] <= 90, "restore tests must occur at least quarterly")

    protection_data = data["data_protection"]
    require(protection_data["restore_target_network_isolated"] is True, "restore targets must be isolated")
    require(protection_data["restored_data_access_limited"] is True, "restored data access must be limited")
    require(protection_data["temporary_restore_cleanup_required"] is True, "temporary restore data must be cleaned up")
    require(
        protection_data["logs_must_not_contain_restored_sensitive_records"] is True,
        "restore validation logs must not contain sensitive records",
    )
    require(protection_data["precise_location_exports_allowed"] is False, "precise location exports are prohibited")
    require(protection_data["raw_payment_instruments_allowed"] is False, "raw payment instruments are prohibited")

    dr = data["disaster_recovery"]
    for key in ("runbook_required", "owner_required", "declaration_criteria_required", "communications_path_required"):
        require(dr[key] is True, f"{key} must be required")
    require(dr["failover_requires_explicit_approval"] is True, "DR failover requires explicit approval")

    evidence = data["evidence"]
    require(evidence["deterministic_restore_contract_validated"] is True, "deterministic contract validation must be recorded")
    for key in (
        "live_production_backup_created",
        "live_production_restore_performed",
        "live_disaster_recovery_exercise_performed",
        "rpo_rto_measured_in_production",
    ):
        require(evidence[key] is False, f"D05 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("no database backup", ("scope", "primary_database_required"), False),
        ("secrets in generic backup", ("scope", "secret_values_in_backup_allowed"), True),
        ("no cross-domain copy", ("protection", "cross_failure_domain_copy_required"), False),
        ("runtime deletes all backups", ("protection", "production_runtime_identity_can_delete_all_backups"), True),
        ("short retention", ("retention", "daily_recovery_points_min"), 2),
        ("weak RPO", ("recovery_objectives", "rpo_minutes_max"), 240),
        ("restore overwrites production", ("restore_validation", "production_overwrite_during_test_allowed"), True),
        ("restore tests too rare", ("restore_validation", "restore_test_interval_days_max"), 365),
        ("restore target not isolated", ("data_protection", "restore_target_network_isolated"), False),
        ("precise-location export", ("data_protection", "precise_location_exports_allowed"), True),
        ("unapproved failover", ("disaster_recovery", "failover_requires_explicit_approval"), False),
        ("false live restore evidence", ("evidence", "live_production_restore_performed"), True),
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
        raise SystemExit(f"negative backup test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 15 production backup contract: valid")


if __name__ == "__main__":
    main()
