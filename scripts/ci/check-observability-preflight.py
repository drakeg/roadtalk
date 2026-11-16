#!/usr/bin/env python3
"""Validate Sprint 16 D05 observability and incident-readiness preflight."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "observability-preflight-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    health = data["health"]
    for key in (
        "liveness_required",
        "readiness_required",
        "database_readiness_required",
        "cache_readiness_required",
        "preflight_health_record_required",
    ):
        require(health[key] is True, f"{key} must be required")
    require(health["optional_dependency_readiness_required"] is False, "optional dependencies must not block core readiness")

    slo = data["slo"]
    require(slo["availability_target_percent_min"] >= 99.5, "availability SLO must be >=99.5%")
    require(slo["latency_p95_ms_max"] <= 1000, "p95 latency target must be <=1000ms")
    require(slo["server_error_rate_percent_max"] <= 1.0, "server error target must be <=1%")
    require(slo["error_budget_required"] is True, "error budget required")
    require(slo["release_block_on_exhausted_error_budget"] is True, "exhausted error budget must block release")
    require(slo["measurement_window_documented_required"] is True, "SLO measurement window must be documented")

    alerts = data["alerts"]
    for key in (
        "delivery_path_required",
        "owner_required",
        "severity_required",
        "runbook_required",
        "deduplication_required",
        "test_notification_required_before_launch",
    ):
        require(alerts[key] is True, f"{key} must be required")
    require(alerts["secret_values_allowed"] is False, "alert secrets prohibited")
    require(alerts["raw_user_payloads_allowed"] is False, "raw user payloads in alerts prohibited")

    incident = data["incident"]
    for key in (
        "incident_owner_required",
        "severity_model_required",
        "escalation_path_required",
        "status_communication_path_required",
        "after_action_review_required",
        "production_incident_exercise_required_before_launch",
    ):
        require(incident[key] is True, f"{key} must be required")

    privacy = data["telemetry_privacy"]
    for key in (
        "raw_authorization_headers_allowed",
        "raw_cookie_headers_allowed",
        "raw_secret_values_allowed",
        "raw_payment_data_allowed",
        "precise_location_allowed",
        "unrelated_user_payloads_allowed",
        "user_identifier_metric_labels_allowed",
        "unbounded_metric_cardinality_allowed",
    ):
        require(privacy[key] is False, f"{key} must be prohibited")

    gate = data["release_gate"]
    require(gate["pre_release_health_required"] is True, "pre-release health required")
    require(gate["post_release_health_required"] is True, "post-release health required")
    require(10 <= gate["minimum_observation_minutes"] <= 60, "observation period must be 10..60 minutes")
    require(gate["failed_health_requires_rollback_or_halt"] is True, "failed health must roll back or halt")
    require(gate["automatic_real_user_rollout_allowed"] is False, "automatic real-user rollout prohibited")

    evidence = data["evidence"]
    require(evidence["deterministic_preflight_validated"] is True, "deterministic preflight must be validated")
    for key in (
        "live_alert_delivery_test_performed",
        "live_slo_measurement_performed",
        "live_incident_exercise_performed",
        "live_release_health_gate_exercised",
    ):
        require(evidence[key] is False, f"D05 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("readiness missing", ("health", "readiness_required"), False),
        ("optional dep blocks readiness", ("health", "optional_dependency_readiness_required"), True),
        ("weak availability SLO", ("slo", "availability_target_percent_min"), 95.0),
        ("missing error budget", ("slo", "error_budget_required"), False),
        ("alert owner missing", ("alerts", "owner_required"), False),
        ("alert secret leak", ("alerts", "secret_values_allowed"), True),
        ("incident escalation missing", ("incident", "escalation_path_required"), False),
        ("incident exercise not required", ("incident", "production_incident_exercise_required_before_launch"), False),
        ("precise location telemetry", ("telemetry_privacy", "precise_location_allowed"), True),
        ("user metric labels", ("telemetry_privacy", "user_identifier_metric_labels_allowed"), True),
        ("auto rollout", ("release_gate", "automatic_real_user_rollout_allowed"), True),
        ("false live incident evidence", ("evidence", "live_incident_exercise_performed"), True),
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
        raise SystemExit(f"negative observability preflight test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 16 observability/incident preflight: valid")


if __name__ == "__main__":
    main()
