#!/usr/bin/env python3
"""Validate Sprint 16 D06 backup/restore/DR readiness boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "backup-restore-preflight-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    restore = data["restore_test"]
    for key in (
        "isolated_target_required",
        "automated_integrity_check_required",
        "schema_validation_required",
        "application_smoke_validation_required",
        "restored_data_access_limited",
        "temporary_cleanup_required",
        "logs_must_not_contain_restored_sensitive_records",
    ):
        require(restore[key] is True, f"{key} must be required")
    require(restore["production_overwrite_allowed"] is False, "production overwrite during restore test prohibited")

    measurement = data["recovery_measurement"]
    require(measurement["target_rpo_minutes_max"] <= 60, "target RPO must be <=60 minutes")
    require(measurement["target_rto_minutes_max"] <= 240, "target RTO must be <=240 minutes")
    for key in (
        "measured_rpo_required_before_launch",
        "measured_rto_required_before_launch",
        "measurement_timestamp_required",
        "recovery_point_timestamp_required",
        "restore_start_timestamp_required",
        "restore_complete_timestamp_required",
    ):
        require(measurement[key] is True, f"{key} must be required")

    integrity = data["backup_integrity"]
    for key in (
        "recovery_point_identity_required",
        "checksum_or_provider_integrity_required",
        "encryption_at_rest_required",
        "encryption_in_transit_required",
        "cross_failure_domain_copy_required",
        "delete_protection_required",
    ):
        require(integrity[key] is True, f"{key} must be required")

    dr = data["dr"]
    for key in (
        "owner_required",
        "declaration_criteria_required",
        "communications_path_required",
        "explicit_failover_approval_required",
        "rollback_target_required",
    ):
        require(dr[key] is True, f"{key} must be required")
    require(dr["destructive_failover_default_allowed"] is False, "destructive failover default prohibited")
    require(dr["production_failover_authorized"] is False, "D06 must not authorize production failover")

    frequency = data["frequency"]
    require(1 <= frequency["restore_test_interval_days_max"] <= 90, "restore test interval must be <=90 days")
    require(frequency["evidence_record_required"] is True, "restore evidence record required")

    evidence = data["evidence"]
    require(evidence["deterministic_preflight_validated"] is True, "deterministic preflight must be validated")
    for key in (
        "live_production_restore_performed",
        "live_disaster_recovery_exercise_performed",
        "production_rpo_measured",
        "production_rto_measured",
    ):
        require(evidence[key] is False, f"D06 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("restore not isolated", ("restore_test", "isolated_target_required"), False),
        ("production overwrite allowed", ("restore_test", "production_overwrite_allowed"), True),
        ("integrity check missing", ("restore_test", "automated_integrity_check_required"), False),
        ("RPO too weak", ("recovery_measurement", "target_rpo_minutes_max"), 120),
        ("RTO too weak", ("recovery_measurement", "target_rto_minutes_max"), 480),
        ("measured RPO not required", ("recovery_measurement", "measured_rpo_required_before_launch"), False),
        ("delete protection missing", ("backup_integrity", "delete_protection_required"), False),
        ("DR approval missing", ("dr", "explicit_failover_approval_required"), False),
        ("production failover authorized", ("dr", "production_failover_authorized"), True),
        ("restore interval too long", ("frequency", "restore_test_interval_days_max"), 180),
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
        raise SystemExit(f"negative backup/restore preflight test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 16 backup/restore/DR preflight: valid")


if __name__ == "__main__":
    main()
