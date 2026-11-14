#!/usr/bin/env python3
"""Validate Sprint 16 D02 public-beta launch authorization boundaries."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "infrastructure" / "environments" / "production" / "launch-authorization.json"

LIVE_AUTH_KEYS = (
    "public_beta_authorized",
    "production_traffic_authorized",
    "dns_cutover_authorized",
    "recurring_spend_authorized",
    "real_money_authorized",
    "provider_activation_authorized",
    "destructive_change_authorized",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_utc(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    require(parsed.tzinfo is not None, f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def validate(data: dict[str, Any], *, now: datetime | None = None) -> None:
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("environment") == "production", "environment must be production")

    authorization = data["authorization"]
    for key in LIVE_AUTH_KEYS:
        require(isinstance(authorization[key], bool), f"{key} must be boolean")

    approval = data["approval"]
    release = data["release_identity"]
    cutover = data["cutover"]
    rollback = data["rollback"]

    require(release["environment"] == "production", "release identity must target production")
    require(0 <= cutover["traffic_percent_max"] <= 100, "traffic_percent_max must be 0..100")
    require(cutover["health_gate_required"] is True, "cutover health gate is required")
    require(cutover["rollback_on_failed_health_required"] is True, "failed health must trigger rollback")

    for key in (
        "named_target_required",
        "exact_digest_required",
        "emergency_disable_required",
        "provider_kill_switch_required",
    ):
        require(rollback[key] is True, f"{key} must be required")

    live_enabled = any(authorization[key] for key in LIVE_AUTH_KEYS)

    if not live_enabled:
        require(cutover["traffic_percent_max"] == 0, "disabled authorization must allow zero traffic")
        require(approval["approval_id"] is None, "disabled authorization must not carry an approval_id")
        require(approval["approved_by"] is None, "disabled authorization must not name an approver")
        require(approval["approved_at"] is None, "disabled authorization must not carry approved_at")
        require(approval["expires_at"] is None, "disabled authorization must not carry expires_at")
        require(approval["scope"] == [], "disabled authorization scope must be empty")
        require(approval["reason"] is None, "disabled authorization must not carry a reason")
        require(release["artifact_digest"] is None, "disabled authorization must not pin a live artifact")
        require(release["terraform_plan_sha256"] is None, "disabled authorization must not pin a live plan")
        require(release["rollback_digest"] is None, "disabled authorization must not pin a live rollback target")
        require(cutover["hostname"] is None, "disabled authorization must not name a live hostname")
        require(cutover["dns_change_id"] is None, "disabled authorization must not carry a DNS change id")
    else:
        require(isinstance(approval["approval_id"], str) and approval["approval_id"].strip(), "approval_id required")
        require(isinstance(approval["approved_by"], str) and approval["approved_by"].strip(), "approved_by required")
        require(isinstance(approval["reason"], str) and approval["reason"].strip(), "approval reason required")
        require(isinstance(approval["scope"], list) and approval["scope"], "non-empty approval scope required")

        approved_at = parse_utc(approval["approved_at"], "approved_at")
        expires_at = parse_utc(approval["expires_at"], "expires_at")
        require(expires_at > approved_at, "authorization expiry must be after approval")
        require((expires_at - approved_at).total_seconds() <= 86400, "authorization may not exceed 24 hours")
        if now is not None:
            require(expires_at > now, "authorization is expired")

        require(
            isinstance(release["artifact_digest"], str)
            and release["artifact_digest"].startswith("sha256:")
            and len(release["artifact_digest"]) == 71,
            "exact immutable artifact digest required",
        )
        require(
            isinstance(release["terraform_plan_sha256"], str)
            and len(release["terraform_plan_sha256"]) == 64,
            "exact Terraform plan SHA-256 required",
        )
        require(
            isinstance(release["rollback_digest"], str)
            and release["rollback_digest"].startswith("sha256:")
            and len(release["rollback_digest"]) == 71,
            "exact rollback digest required",
        )
        require(release["artifact_digest"] != release["rollback_digest"], "rollback digest must differ from release digest")

        if authorization["public_beta_authorized"] or authorization["production_traffic_authorized"]:
            require(1 <= cutover["traffic_percent_max"] <= 100, "authorized traffic requires an explicit bounded percentage")
        else:
            require(cutover["traffic_percent_max"] == 0, "traffic must stay zero unless traffic is authorized")

        if authorization["dns_cutover_authorized"]:
            require(isinstance(cutover["hostname"], str) and cutover["hostname"].strip(), "DNS authorization requires hostname")
            require(isinstance(cutover["dns_change_id"], str) and cutover["dns_change_id"].strip(), "DNS authorization requires change id")

        scope = set(approval["scope"])
        for key in LIVE_AUTH_KEYS:
            if authorization[key]:
                require(key in scope, f"approval scope missing enabled authorization: {key}")

    evidence = data["evidence"]
    require(evidence["authorization_contract_validated"] is True, "authorization contract validation must be recorded")
    for key in (
        "live_public_beta_started",
        "live_production_traffic_shifted",
        "live_dns_cutover_performed",
        "live_recurring_spend_started",
    ):
        require(evidence[key] is False, f"D02 must not claim {key}")


def enabled_fixture(data: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(data)
    candidate["authorization"]["public_beta_authorized"] = True
    candidate["authorization"]["production_traffic_authorized"] = True
    candidate["approval"] = {
        "approval_id": "S16-test-approval",
        "approved_by": "named-approver",
        "approved_at": "2030-01-01T00:00:00Z",
        "expires_at": "2030-01-01T01:00:00Z",
        "scope": ["public_beta_authorized", "production_traffic_authorized"],
        "reason": "deterministic self-test only"
    }
    candidate["release_identity"]["artifact_digest"] = "sha256:" + "a" * 64
    candidate["release_identity"]["terraform_plan_sha256"] = "b" * 64
    candidate["release_identity"]["rollback_digest"] = "sha256:" + "c" * 64
    candidate["cutover"]["traffic_percent_max"] = 5
    return candidate


def run_self_test(data: dict[str, Any]) -> None:
    validate(data)

    cases: list[tuple[str, tuple[str, ...], Any]] = [
        ("default traffic enabled", ("authorization", "production_traffic_authorized"), True),
        ("disabled traffic percentage", ("cutover", "traffic_percent_max"), 1),
        ("false live evidence", ("evidence", "live_public_beta_started"), True),
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
        raise SystemExit(f"negative authorization test unexpectedly accepted: {label}")

    base = enabled_fixture(data)
    validate(base, now=datetime(2029, 12, 31, tzinfo=timezone.utc))

    enabled_cases: list[tuple[str, tuple[str, ...], Any]] = [
        ("missing approver", ("approval", "approved_by"), None),
        ("empty scope", ("approval", "scope"), []),
        ("expired approval", ("approval", "expires_at"), "2029-01-01T00:00:00Z"),
        ("mutable artifact", ("release_identity", "artifact_digest"), "latest"),
        ("missing rollback", ("release_identity", "rollback_digest"), None),
        ("unbounded traffic", ("cutover", "traffic_percent_max"), 101),
        ("scope mismatch", ("approval", "scope"), ["public_beta_authorized"]),
    ]
    for label, path, value in enabled_cases:
        candidate = copy.deepcopy(base)
        target: Any = candidate
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        try:
            validate(candidate, now=datetime(2029, 12, 31, tzinfo=timezone.utc))
        except (ValueError, TypeError):
            continue
        raise SystemExit(f"negative enabled-authorization test unexpectedly accepted: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    data = json.loads(CONTRACT.read_text())
    validate(data)
    if args.self_test:
        run_self_test(data)
    print("Sprint 16 launch authorization contract: valid and disabled")


if __name__ == "__main__":
    main()
