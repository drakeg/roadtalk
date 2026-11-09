#!/usr/bin/env python3
"""Validate the Sprint 15 production environment/deployment contract."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "production-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be explicit production")
    for flag in (
        "deployment_authorized",
        "public_beta_authorized",
        "dns_cutover_authorized",
        "recurring_spend_authorized",
    ):
        require(data.get(flag) is False, f"{flag} must remain false in D02")

    separation = data["environment_separation"]
    require(separation["terraform_workspace_reuse"] is False, "production must not reuse Terraform workspaces")
    require(separation["field_test_state_reuse"] is False, "production must not reuse field-test state")
    require(separation["field_test_network_reuse"] is False, "production must not reuse field-test networking")
    require(separation["production_state_key"] == "production/terraform.tfstate", "production state key must be explicit")
    require(separation["production_parameter_prefix"] == "/roadtalk/production/", "production secret prefix must be explicit")

    topology = data["topology"]
    require(topology["availability_zones_minimum"] >= 2, "production topology requires at least two AZs")
    require(topology["single_host_allowed"] is False, "single-host production topology is prohibited")
    require(topology["public_database_allowed"] is False, "public production databases are prohibited")
    require(topology["public_cache_allowed"] is False, "public production caches are prohibited")
    require(topology["ingress"] == "managed-load-balancer", "production ingress must be explicit")
    require(topology["compute"] == "private-subnet-service", "production compute must be private")

    tls = data["domains_tls"]
    require(tls["domain_configuration_mode"] == "explicit-approved-input", "production domain must be an explicit approved input")
    require(tls["domain_ownership_required"] is True, "domain ownership verification is required")
    require(tls["tls_required"] is True, "TLS is required")
    require(tls["minimum_tls_version"] in {"1.2", "1.3"}, "minimum TLS version must be 1.2 or newer")
    require(tls["http_to_https_redirect_required"] is True, "HTTP must redirect to HTTPS")
    require(tls["certificate_validation_required"] is True, "certificate validation is required")

    artifacts = data["artifacts"]
    require(artifacts["backend_image_selector"] == "sha256-digest", "backend image selection must use an immutable digest")
    require(artifacts["mutable_tags_allowed"] is False, "mutable image tags are prohibited")
    require(artifacts["provenance_required"] is True, "artifact provenance is required")
    require(artifacts["rollback_artifact_required"] is True, "a rollback artifact is required")

    config = data["configuration"]
    require(config["runtime_environment_value"] == "production", "runtime environment must be production")
    require(config["plaintext_secrets_in_terraform"] is False, "plaintext Terraform secrets are prohibited")
    require(config["plaintext_secrets_in_ci"] is False, "plaintext CI secrets are prohibited")
    require(config["managed_secret_source_required"] is True, "a managed production secret source is required")
    for provider in ("premium_provider_default", "payment_provider_default", "store_provider_default"):
        require(config[provider] == "disabled", f"{provider} must default disabled")

    release = data["release"]
    for gate in (
        "manual_approval_required",
        "exact_artifact_required",
        "exact_plan_required",
        "database_migration_check_required",
        "rollback_target_required",
        "emergency_disable_required",
    ):
        require(release[gate] is True, f"{gate} must be required")
    require(release["automatic_real_user_rollout_allowed"] is False, "automatic real-user rollout is prohibited")
    require(
        release["irreversible_migration_blocks_automatic_rollback"] is True,
        "irreversible migrations must block automatic rollback",
    )

    evidence = data["evidence"]
    require(evidence["ci_is_live_production_evidence"] is False, "CI must not be represented as live production evidence")
    require(evidence["simulation_is_live_production_evidence"] is False, "simulation must not be represented as live production evidence")
    for key in (
        "live_load_test_performed",
        "live_failover_performed",
        "live_disaster_recovery_performed",
        "production_traffic_performed",
    ):
        require(evidence[key] is False, f"D02 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("ambiguous environment", ("environment",), "prod"),
        ("deployment authorization", ("deployment_authorized",), True),
        ("workspace reuse", ("environment_separation", "terraform_workspace_reuse"), True),
        ("single host", ("topology", "single_host_allowed"), True),
        ("public database", ("topology", "public_database_allowed"), True),
        ("weak TLS", ("domains_tls", "minimum_tls_version"), "1.1"),
        ("mutable artifact", ("artifacts", "mutable_tags_allowed"), True),
        ("plaintext secret", ("configuration", "plaintext_secrets_in_ci"), True),
        ("automatic rollout", ("release", "automatic_real_user_rollout_allowed"), True),
        ("false live evidence", ("evidence", "production_traffic_performed"), True),
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
        raise SystemExit(f"negative contract test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 15 production contract: valid")


if __name__ == "__main__":
    main()
