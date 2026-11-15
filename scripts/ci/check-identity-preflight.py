#!/usr/bin/env python3
"""Validate Sprint 16 D04 production identity/secrets preflight boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "identity-preflight-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    oidc = data["oidc"]
    require(oidc["provider"] == "github-actions-oidc", "GitHub Actions OIDC required")
    require(oidc["repository"] == "drakeg/roadtalk", "OIDC repository must be scoped")
    require(oidc["branch"] == "main", "OIDC branch must be main")
    require(oidc["audience"] == "sts.amazonaws.com", "OIDC audience must target STS")
    require(oidc["pull_request_deploy_allowed"] is False, "PR deploy must remain prohibited")
    require(oidc["shared_static_credentials_allowed"] is False, "shared static credentials prohibited")
    require(oidc["long_lived_access_keys_allowed"] is False, "long-lived access keys prohibited")
    require(1 <= oidc["session_duration_minutes_max"] <= 60, "OIDC session must be bounded to <=60 minutes")

    roles = data["roles"]
    require(roles["separate_plan_and_apply_roles_required"] is True, "separate plan/apply roles required")
    require(roles["apply_role_manual_approval_required"] is True, "apply role manual approval required")
    require(roles["wildcard_actions_allowed"] is False, "wildcard actions prohibited")
    require(roles["wildcard_resources_allowed"] is False, "wildcard resources prohibited")
    require(roles["administrator_access_allowed"] is False, "AdministratorAccess prohibited")
    require(roles["runtime_role_can_modify_iam"] is False, "runtime IAM mutation prohibited")
    require(roles["runtime_role_can_read_unscoped_secrets"] is False, "unscoped secret reads prohibited")

    secrets = data["secrets"]
    require(secrets["managed_store_required"] is True, "managed secret store required")
    require(secrets["parameter_prefix"] == "/roadtalk/production/", "production secret prefix must be scoped")
    require(secrets["runtime_fetch_required"] is True, "runtime secret fetch required")
    require(secrets["plaintext_repository_allowed"] is False, "plaintext repository secrets prohibited")
    require(secrets["plaintext_ci_logs_allowed"] is False, "plaintext CI secrets prohibited")
    require(secrets["plaintext_terraform_state_allowed"] is False, "plaintext Terraform-state secrets prohibited")
    require(1 <= secrets["rotation_days_max"] <= 90, "secret rotation interval must be <=90 days")
    require(secrets["rotation_owner_required"] is True, "secret rotation owner required")
    require(secrets["provider_credentials_separate_approval_required"] is True, "provider credentials need separate approval")

    human = data["human_access"]
    require(human["individual_identity_required"] is True, "individual human identities required")
    require(human["mfa_required"] is True, "human MFA required")
    require(human["shared_users_allowed"] is False, "shared human users prohibited")
    require(human["direct_long_lived_keys_allowed"] is False, "direct long-lived human keys prohibited")
    require(1 <= human["access_review_interval_days_max"] <= 90, "access review must be <=90 days")

    bg = data["break_glass"]
    require(bg["enabled"] is True, "break-glass path required")
    require(bg["shared_account_allowed"] is False, "shared break-glass account prohibited")
    require(bg["mfa_required"] is True, "break-glass MFA required")
    require(bg["reason_required"] is True, "break-glass reason required")
    require(bg["ticket_or_incident_id_required"] is True, "break-glass ticket/incident ID required")
    require(bg["time_bounded_required"] is True, "break-glass session must be time-bounded")
    require(1 <= bg["session_minutes_max"] <= 60, "break-glass session must be <=60 minutes")
    require(bg["audit_log_required"] is True, "break-glass audit log required")
    require(bg["post_use_review_required"] is True, "break-glass post-use review required")
    require(bg["standing_admin_session_allowed"] is False, "standing admin session prohibited")

    evidence = data["evidence"]
    require(evidence["deterministic_preflight_validated"] is True, "deterministic preflight validation required")
    for key in (
        "live_oidc_assume_role_test_performed",
        "live_secret_rotation_test_performed",
        "live_break_glass_exercise_performed",
        "live_access_review_performed",
    ):
        require(evidence[key] is False, f"D04 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("PR deploy allowed", ("oidc", "pull_request_deploy_allowed"), True),
        ("static credentials allowed", ("oidc", "shared_static_credentials_allowed"), True),
        ("long session", ("oidc", "session_duration_minutes_max"), 120),
        ("wildcard actions", ("roles", "wildcard_actions_allowed"), True),
        ("admin access", ("roles", "administrator_access_allowed"), True),
        ("unscoped secrets", ("roles", "runtime_role_can_read_unscoped_secrets"), True),
        ("plaintext repo secret", ("secrets", "plaintext_repository_allowed"), True),
        ("rotation too long", ("secrets", "rotation_days_max"), 365),
        ("shared human user", ("human_access", "shared_users_allowed"), True),
        ("break glass no MFA", ("break_glass", "mfa_required"), False),
        ("standing admin", ("break_glass", "standing_admin_session_allowed"), True),
        ("false live OIDC evidence", ("evidence", "live_oidc_assume_role_test_performed"), True),
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
        raise SystemExit(f"negative identity preflight test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 16 identity/secrets/break-glass preflight: valid")


if __name__ == "__main__":
    main()
