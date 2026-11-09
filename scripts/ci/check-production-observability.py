#!/usr/bin/env python3
"""Validate Sprint 15 D04 observability and operational-health boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "observability-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    health = data["health"]
    require(health["liveness_required"] is True, "liveness is required")
    require(health["readiness_required"] is True, "readiness is required")
    require(health["readiness_checks_database"] is True, "readiness must check database")
    require(health["readiness_checks_cache"] is True, "readiness must check cache")
    require(health["readiness_checks_external_optional_dependencies"] is False, "optional external dependencies must not make readiness flap")
    require(health["health_endpoint_contains_secret_data"] is False, "health endpoints must not expose secrets")
    require(health["health_endpoint_contains_user_data"] is False, "health endpoints must not expose user data")

    logging = data["logging"]
    for key in ("structured_json_required", "request_id_required", "service_name_required", "environment_required", "severity_required"):
        require(logging[key] is True, f"{key} must be required")
    for key in (
        "raw_authorization_header_allowed",
        "raw_cookie_header_allowed",
        "raw_secret_values_allowed",
        "raw_payment_data_allowed",
        "precise_location_allowed",
        "unrelated_user_payloads_allowed",
    ):
        require(logging[key] is False, f"{key} must remain false")
    require(1 <= logging["retention_days_max"] <= 30, "log retention must be bounded to 30 days or less")

    metrics = data["metrics"]
    for key in ("request_rate_required", "error_rate_required", "latency_required", "dependency_health_required", "resource_saturation_required"):
        require(metrics[key] is True, f"{key} must be required")
    for key in ("user_id_labels_allowed", "email_labels_allowed", "precise_location_labels_allowed", "unbounded_cardinality_allowed"):
        require(metrics[key] is False, f"{key} must remain false")

    alerts = data["alerts"]
    for key in ("owner_required", "runbook_required", "severity_required", "duplicate_storm_protection_required"):
        require(alerts[key] is True, f"{key} must be required")
    require(alerts["secret_values_allowed"] is False, "alerts must not contain secret values")
    require(alerts["raw_user_payloads_allowed"] is False, "alerts must not contain raw user payloads")

    slo = data["slo"]
    require(99.0 <= slo["availability_target_percent_min"] <= 100.0, "availability target must be realistic and bounded")
    require(1 <= slo["latency_p95_ms_max"] <= 5000, "p95 latency target must be bounded")
    require(0 < slo["server_error_rate_percent_max"] <= 5.0, "server error target must be bounded")
    require(slo["error_budget_required"] is True, "error budget is required")
    require(slo["release_block_on_exhausted_error_budget"] is True, "release must block on exhausted error budget")

    gate = data["release_health_gate"]
    require(gate["pre_release_health_check_required"] is True, "pre-release health check required")
    require(gate["post_release_health_check_required"] is True, "post-release health check required")
    require(gate["rollback_on_failed_health_required"] is True, "failed health must require rollback")
    require(5 <= gate["minimum_observation_minutes"] <= 60, "observation window must be 5-60 minutes")
    require(gate["automatic_real_user_rollout_allowed"] is False, "automatic real-user rollout remains prohibited")

    evidence = data["evidence"]
    for key in (
        "live_production_metrics_collected",
        "live_production_alerts_fired",
        "live_production_slo_measured",
        "live_production_release_gate_exercised",
    ):
        require(evidence[key] is False, f"D04 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("missing readiness", ("health", "readiness_required"), False),
        ("health leaks user data", ("health", "health_endpoint_contains_user_data"), True),
        ("authorization header logging", ("logging", "raw_authorization_header_allowed"), True),
        ("precise location logging", ("logging", "precise_location_allowed"), True),
        ("user-id metric labels", ("metrics", "user_id_labels_allowed"), True),
        ("unbounded metrics", ("metrics", "unbounded_cardinality_allowed"), True),
        ("alerts without owner", ("alerts", "owner_required"), False),
        ("alerts include secrets", ("alerts", "secret_values_allowed"), True),
        ("no error budget", ("slo", "error_budget_required"), False),
        ("automatic rollout", ("release_health_gate", "automatic_real_user_rollout_allowed"), True),
        ("false live evidence", ("evidence", "live_production_slo_measured"), True),
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
        raise SystemExit(f"negative observability test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 15 production observability contract: valid")


if __name__ == "__main__":
    main()
