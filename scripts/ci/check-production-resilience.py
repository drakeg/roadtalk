#!/usr/bin/env python3
"""Validate Sprint 15 D07 production scale/resilience boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "resilience-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    capacity = data["capacity"]
    require(capacity["documented_capacity_model_required"] is True, "capacity model required")
    require(20 <= capacity["headroom_percent_min"] <= 80, "capacity headroom must be bounded")
    require(capacity["single_instance_capacity_assumption_allowed"] is False, "single-instance capacity assumption prohibited")
    require(capacity["bounded_concurrency_required"] is True, "bounded concurrency required")
    require(capacity["bounded_queue_depth_required"] is True, "bounded queue depth required")
    require(capacity["unbounded_retry_allowed"] is False, "unbounded retries prohibited")

    rate = data["rate_limits"]
    for key in (
        "public_api_rate_limit_required",
        "authenticated_abuse_limit_required",
        "per_identity_burst_limit_required",
        "retry_after_required",
    ):
        require(rate[key] is True, f"{key} must be required")
    require(rate["rate_limit_bypass_default_allowed"] is False, "rate-limit bypass must default deny")

    dep = data["dependency_failures"]
    for key in (
        "timeouts_required",
        "bounded_retries_required",
        "exponential_backoff_required",
        "circuit_breaker_or_fail_fast_required",
        "external_provider_failure_requires_graceful_degradation",
    ):
        require(dep[key] is True, f"{key} must be required")
    require(dep["optional_dependency_failure_blocks_core_readiness"] is False, "optional dependency failure must not block core readiness")

    db = data["database"]
    for key in (
        "connection_pool_bounds_required",
        "query_timeout_required",
        "multi_az_required",
        "automatic_failover_capability_required",
        "application_retry_on_failover_bounded",
    ):
        require(db[key] is True, f"{key} must be required")

    network = data["network"]
    require(network["multi_az_ingress_required"] is True, "multi-AZ ingress required")
    require(network["health_based_target_removal_required"] is True, "health-based target removal required")
    require(network["single_az_dependency_allowed"] is False, "single-AZ dependency prohibited")
    require(network["unbounded_connection_lifetime_allowed"] is False, "unbounded connection lifetime prohibited")

    degrade = data["graceful_degradation"]
    for key, value in degrade.items():
        require(value is True, f"{key} must be required")

    bounds = data["resource_bounds"]
    for key, value in bounds.items():
        require(value is True, f"{key} must be required")

    evidence = data["evidence"]
    require(evidence["deterministic_resilience_contract_validated"] is True, "deterministic resilience validation required")
    for key in (
        "live_load_test_performed",
        "live_database_failover_performed",
        "live_az_failure_performed",
        "live_dependency_chaos_test_performed",
    ):
        require(evidence[key] is False, f"D07 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("single-instance capacity", ("capacity", "single_instance_capacity_assumption_allowed"), True),
        ("unbounded retry", ("capacity", "unbounded_retry_allowed"), True),
        ("no public rate limit", ("rate_limits", "public_api_rate_limit_required"), False),
        ("rate-limit bypass", ("rate_limits", "rate_limit_bypass_default_allowed"), True),
        ("no timeout", ("dependency_failures", "timeouts_required"), False),
        ("optional dependency blocks readiness", ("dependency_failures", "optional_dependency_failure_blocks_core_readiness"), True),
        ("single-AZ database", ("database", "multi_az_required"), False),
        ("single-AZ dependency", ("network", "single_az_dependency_allowed"), True),
        ("no graceful AI degradation", ("graceful_degradation", "ai_provider_failure_disables_ai_features"), False),
        ("no worker bound", ("resource_bounds", "worker_concurrency_limit_required"), False),
        ("false live failover evidence", ("evidence", "live_database_failover_performed"), True),
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
        raise SystemExit(f"negative resilience test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 15 production resilience contract: valid")


if __name__ == "__main__":
    main()
