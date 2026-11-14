#!/usr/bin/env python3
"""Validate Sprint 16 D03 DNS/TLS/public-ingress readiness boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "dns-tls-ingress-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    dns = data["dns"]
    for key in (
        "ownership_verified_required",
        "authoritative_zone_required",
        "hostname_required_before_cutover",
        "change_id_required_before_cutover",
    ):
        require(dns[key] is True, f"{key} must be required")
    require(30 <= dns["ttl_seconds_max"] <= 300, "DNS TTL maximum must be 30..300 seconds")
    require(dns["cutover_authorized"] is False, "D03 must not authorize DNS cutover")

    tls = data["tls"]
    for key in (
        "certificate_required",
        "certificate_validation_required",
        "hostname_match_required",
        "http_to_https_redirect_required",
    ):
        require(tls[key] is True, f"{key} must be required")
    require(tls["minimum_tls_version"] in ("1.2", "1.3"), "minimum TLS must be 1.2 or newer")
    require(7 <= tls["certificate_expiry_days_min"] <= 90, "certificate minimum remaining lifetime must be 7..90 days")

    ingress = data["ingress"]
    require(ingress["managed_load_balancer_required"] is True, "managed load balancer required")
    require(ingress["multi_az_required"] is True, "multi-AZ ingress required")
    require(ingress["public_database_allowed"] is False, "public database prohibited")
    require(ingress["public_cache_allowed"] is False, "public cache prohibited")
    require(ingress["health_check_required"] is True, "health check required")
    require(ingress["unhealthy_target_removal_required"] is True, "unhealthy target removal required")

    cutover = data["cutover"]
    for key in (
        "pre_health_check_required",
        "post_health_check_required",
        "rollback_plan_required",
        "rollback_dns_target_required",
        "traffic_ramp_required",
    ):
        require(cutover[key] is True, f"{key} must be required")
    require(1 <= cutover["initial_traffic_percent_max"] <= 25, "initial traffic ramp must be 1..25%")
    require(5 <= cutover["observation_minutes_min"] <= 60, "observation minimum must be 5..60 minutes")
    require(cutover["automatic_full_cutover_allowed"] is False, "automatic full cutover prohibited")

    rollback = data["rollback"]
    for key in (
        "dns_revert_required",
        "previous_target_record_required",
        "certificate_rollback_considered",
        "emergency_disable_required",
    ):
        require(rollback[key] is True, f"{key} must be required")

    evidence = data["evidence"]
    require(evidence["deterministic_preflight_validated"] is True, "deterministic preflight validation required")
    for key in (
        "live_dns_cutover_performed",
        "live_certificate_validation_performed",
        "live_public_ingress_exercised",
        "real_user_traffic_shifted",
    ):
        require(evidence[key] is False, f"D03 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("DNS ownership missing", ("dns", "ownership_verified_required"), False),
        ("DNS cutover enabled", ("dns", "cutover_authorized"), True),
        ("TTL too high", ("dns", "ttl_seconds_max"), 3600),
        ("certificate validation missing", ("tls", "certificate_validation_required"), False),
        ("TLS downgrade", ("tls", "minimum_tls_version"), "1.1"),
        ("single-AZ ingress", ("ingress", "multi_az_required"), False),
        ("public database", ("ingress", "public_database_allowed"), True),
        ("no rollback plan", ("cutover", "rollback_plan_required"), False),
        ("full automatic cutover", ("cutover", "automatic_full_cutover_allowed"), True),
        ("traffic ramp too high", ("cutover", "initial_traffic_percent_max"), 100),
        ("no previous DNS target", ("rollback", "previous_target_record_required"), False),
        ("false live DNS evidence", ("evidence", "live_dns_cutover_performed"), True),
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
        raise SystemExit(f"negative DNS/TLS/ingress test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 16 DNS/TLS/public-ingress contract: valid and cutover disabled")


if __name__ == "__main__":
    main()
