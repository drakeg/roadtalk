#!/usr/bin/env python3
"""Validate Sprint 16 D07 load/failover/degraded-mode readiness."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "resilience-preflight-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    load = data["load_test"]
    for key in ("profile_required", "environment_required", "operator_required"):
        require(load[key] is True, f"{key} must be required")
    require(1 <= load["duration_minutes_max"] <= 30, "duration must be bounded to <=30 minutes")
    require(1 <= load["concurrency_max"] <= 500, "concurrency must be bounded to <=500")
    require(1 <= load["request_rate_per_second_max"] <= 250, "request rate must be bounded to <=250 rps")
    require(0 < load["error_rate_abort_percent"] <= 5.0, "error abort threshold must be <=5%")
    require(100 <= load["latency_p95_abort_ms"] <= 2000, "p95 latency abort threshold must be <=2000 ms")
    require(0 < load["cost_guard_usd_max"] <= 25, "cost guard must be <=$25")
    require(load["automatic_production_execution_allowed"] is False, "automatic production load tests prohibited")

    failures = data["failure_scenarios"]
    for key in (
        "database_failover_profile_required",
        "az_failure_profile_required",
        "cache_failure_profile_required",
        "external_provider_failure_profile_required",
        "network_partition_profile_required",
    ):
        require(failures[key] is True, f"{key} must be required")
    require(failures["destructive_failure_injection_default_allowed"] is False, "destructive failure injection default prohibited")
    require(failures["production_failure_injection_authorized"] is False, "D07 must not authorize production failure injection")

    stop = data["stop_conditions"]
    for key in (
        "health_gate_failure_stops_test",
        "error_budget_breach_stops_test",
        "security_or_privacy_signal_stops_test",
        "operator_abort_required",
        "cost_guard_breach_stops_test",
    ):
        require(stop[key] is True, f"{key} must be required")

    degraded = data["degraded_mode"]
    for key in (
        "core_read_path_preserved_when_optional_features_fail",
        "premium_provider_failure_disables_premium_actions",
        "notification_provider_failure_queues_or_drops_safely",
        "ai_provider_failure_disables_ai_features",
        "location_provider_failure_preserves_non_location_features",
    ):
        require(degraded[key] is True, f"{key} must be required")

    evidence = data["evidence"]
    require(evidence["deterministic_preflight_validated"] is True, "deterministic preflight must be validated")
    for key in (
        "live_load_test_performed",
        "live_database_failover_performed",
        "live_az_failure_performed",
        "live_dependency_failure_exercise_performed",
        "production_failure_injection_performed",
    ):
        require(evidence[key] is False, f"D07 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("unbounded duration", ("load_test", "duration_minutes_max"), 120),
        ("unbounded concurrency", ("load_test", "concurrency_max"), 5000),
        ("weak error stop", ("load_test", "error_rate_abort_percent"), 20.0),
        ("no cost guard", ("load_test", "cost_guard_usd_max"), 1000),
        ("automatic prod load", ("load_test", "automatic_production_execution_allowed"), True),
        ("missing DB failover profile", ("failure_scenarios", "database_failover_profile_required"), False),
        ("destructive default enabled", ("failure_scenarios", "destructive_failure_injection_default_allowed"), True),
        ("production failure injection enabled", ("failure_scenarios", "production_failure_injection_authorized"), True),
        ("no privacy stop", ("stop_conditions", "security_or_privacy_signal_stops_test"), False),
        ("premium does not degrade", ("degraded_mode", "premium_provider_failure_disables_premium_actions"), False),
        ("false live load evidence", ("evidence", "live_load_test_performed"), True),
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
        raise SystemExit(f"negative resilience preflight test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 16 load/failover/degraded-mode preflight: valid")


if __name__ == "__main__":
    main()
