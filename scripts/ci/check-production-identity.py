#!/usr/bin/env python3
"""Validate Sprint 15 D03 production IAM/secrets boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "identity-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    ci = data["ci_identity"]
    require(ci["provider"] == "github-actions-oidc", "CI must use GitHub Actions OIDC")
    require(ci["shared_static_credentials_allowed"] is False, "shared static CI credentials are prohibited")
    require(ci["long_lived_access_keys_allowed"] is False, "long-lived CI access keys are prohibited")
    require(ci["audience"] == "sts.amazonaws.com", "OIDC audience must be AWS STS")
    require(ci["repository"] == "drakeg/roadtalk", "OIDC trust must be repository-scoped")
    require(ci["branch"] == "main", "production deploy trust must be main-scoped")
    require(ci["pull_request_deploy_allowed"] is False, "pull requests must not deploy production")
    require(1 <= ci["session_duration_minutes_max"] <= 60, "CI session duration must be bounded to 60 minutes or less")

    least = data["least_privilege"]
    require(least["wildcard_actions_allowed"] is False, "IAM wildcard actions are prohibited")
    require(least["wildcard_resources_allowed"] is False, "IAM wildcard resources are prohibited")
    require(least["administrator_access_allowed"] is False, "AdministratorAccess is prohibited")
    require(least["separate_plan_and_apply_roles_required"] is True, "plan and apply identities must be separate")
    require(least["apply_role_requires_manual_approval"] is True, "production apply requires manual approval")
    require(least["runtime_role_cannot_modify_iam"] is True, "runtime role must not modify IAM")
    require(least["runtime_role_cannot_read_unscoped_secrets"] is True, "runtime role secret reads must be scoped")

    secrets = data["secrets"]
    require(secrets["source"] == "managed-secret-store", "production secrets require a managed secret store")
    require(secrets["parameter_prefix"] == "/roadtalk/production/", "secret namespace must be production-scoped")
    require(secrets["plaintext_in_repository_allowed"] is False, "plaintext repository secrets are prohibited")
    require(secrets["plaintext_in_ci_logs_allowed"] is False, "plaintext CI log secrets are prohibited")
    require(secrets["plaintext_in_terraform_state_allowed"] is False, "plaintext Terraform-state secrets are prohibited")
    require(secrets["runtime_fetch_required"] is True, "runtime secret fetch is required")
    require(1 <= secrets["rotation_days_max"] <= 90, "secret rotation must be 90 days or less")
    require(secrets["provider_credentials_separately_approved"] is True, "provider credentials require separate approval")

    bg = data["break_glass"]
    require(bg["enabled"] is True, "break-glass process must be defined")
    require(bg["shared_account_allowed"] is False, "shared break-glass accounts are prohibited")
    require(bg["mfa_required"] is True, "break-glass MFA is required")
    require(bg["time_bounded_required"] is True, "break-glass access must be time bounded")
    require(bg["reason_required"] is True, "break-glass reason is required")
    require(bg["audit_log_required"] is True, "break-glass auditing is required")
    require(bg["post_use_review_required"] is True, "break-glass use requires review")
    require(bg["standing_admin_session_allowed"] is False, "standing admin sessions are prohibited")

    human = data["human_access"]
    require(human["individual_identity_required"] is True, "human access must use individual identities")
    require(human["mfa_required"] is True, "human MFA is required")
    require(human["shared_users_allowed"] is False, "shared users are prohibited")
    require(human["direct_long_lived_keys_allowed"] is False, "human long-lived keys are prohibited")

    evidence = data["evidence"]
    for key in (
        "live_production_role_created",
        "live_secret_created",
        "live_oidc_trust_created",
        "live_break_glass_exercised",
    ):
        require(evidence[key] is False, f"D03 must not claim {key}")


def run_self_test(data: dict[str, Any]) -> None:
    cases = [
        ("static CI credentials", ("ci_identity", "shared_static_credentials_allowed"), True),
        ("long-lived CI keys", ("ci_identity", "long_lived_access_keys_allowed"), True),
        ("PR production deploy", ("ci_identity", "pull_request_deploy_allowed"), True),
        ("admin access", ("least_privilege", "administrator_access_allowed"), True),
        ("wildcard actions", ("least_privilege", "wildcard_actions_allowed"), True),
        ("unscoped secret reads", ("least_privilege", "runtime_role_cannot_read_unscoped_secrets"), False),
        ("plaintext repo secret", ("secrets", "plaintext_in_repository_allowed"), True),
        ("weak rotation", ("secrets", "rotation_days_max"), 365),
        ("break-glass no MFA", ("break_glass", "mfa_required"), False),
        ("shared human user", ("human_access", "shared_users_allowed"), True),
        ("false live identity evidence", ("evidence", "live_oidc_trust_created"), True),
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
        raise SystemExit(f"negative identity test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 15 production identity contract: valid")


if __name__ == "__main__":
    main()
