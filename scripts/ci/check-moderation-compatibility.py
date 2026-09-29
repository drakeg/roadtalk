#!/usr/bin/env python3
"""Fail CI if Sprint 12 moderation compatibility, privacy, or $0 provider boundaries regress."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Moderation compatibility gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return target.read_text(encoding="utf-8")


def normalized(path: str) -> str:
    return " ".join(read(path).lower().split())


implementation_paths = (
    "backend/app/api/moderation.py",
    "backend/app/moderation/contracts.py",
    "backend/app/moderation/limiter.py",
    "backend/app/moderation/service.py",
    "backend/app/moderation_web.py",
    "mobile/src/moderation/api.ts",
    "mobile/src/screens/SafetyScreen.tsx",
)
implementation = "\n".join(read(path).lower() for path in implementation_paths)

for forbidden in (
    "boto3",
    "botocore",
    "requests.",
    "httpx.",
    "aiohttp.",
    "urllib.request",
    "openai",
    "anthropic",
    "moderation provider",
    "moderation_provider",
    "perspective api",
    "rekognition",
    "comprehend",
):
    if forbidden in implementation:
        fail(f"moderation implementation references external provider/network capability {forbidden!r}")

contracts = read("backend/app/moderation/contracts.py").lower()
for required in (
    "latitude",
    "longitude",
    "route_history",
    "audio_recording",
    "transcript",
    "access_token",
    "refresh_token",
    "provider_token",
    "api_key",
    "enforcement_override",
    "authorization_override",
):
    if required not in contracts:
        fail(f"moderation prohibited-field contract no longer names {required!r}")

service = read("backend/app/moderation/service.py")
for required in (
    "except IntegrityError",
    "await db.rollback()",
    'ReportLifecycleError("report unavailable")',
    'RestrictionLifecycleError("moderation unavailable")',
):
    if required not in service:
        fail(f"moderation race hardening no longer contains {required!r}")

authorization = read("backend/app/ptt/proximity.py")
for required in (
    "filter_moderation_receive_grants",
    'ModerationRestriction.state == "active"',
    "ModerationRestriction.expires_at",
):
    if required not in authorization:
        fail(f"server moderation authorization no longer enforces {required!r}")

for path, required_tests in {
    "backend/tests/test_moderation_contracts.py": (
        "test_report_command_is_closed_bounded_and_has_no_sensitive_evidence",
        "test_restriction_command_cannot_target_arbitrary_audiences",
    ),
    "backend/tests/test_moderation_authorization.py": (
        "test_moderation_filter_never_adds_upstream_ineligible_recipient",
        "test_receiver_mute_or_block_of_sender_denies_delivery",
    ),
    "backend/tests/test_moderation_hardening.py": (
        "test_concurrent_identical_report_replays_after_unique_conflict",
        "test_concurrent_mismatched_report_fails_with_generic_error",
        "test_concurrent_identical_restriction_replays_after_unique_conflict",
        "test_concurrent_restriction_conflict_fails_with_generic_error",
    ),
    "mobile/src/__tests__/ModerationApi.test.ts": (
        "uses authenticated endpoints with only bounded payload fields",
        "fails closed on unavailable moderation endpoints",
    ),
}.items():
    content = read(path)
    for name in required_tests:
        if name not in content:
            fail(f"{path} is missing required Sprint 12 coverage {name!r}")

backend = tomllib.loads(read("backend/pyproject.toml"))
backend_dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0].lower()
    for dependency in backend["project"]["dependencies"]
}
mobile_dependencies = set(json.loads(read("mobile/package.json"))["dependencies"])
for forbidden in (
    "boto3",
    "openai",
    "anthropic",
    "google-cloud-aiplatform",
    "azure-ai-contentsafety",
    "@aws-sdk/client-rekognition",
):
    if forbidden in backend_dependencies or forbidden in mobile_dependencies:
        fail(f"unapproved moderation/cloud dependency detected: {forbidden}")

for path in (
    "infrastructure/bootstrap",
    "infrastructure/environments/field-test",
    "infrastructure/modules",
):
    base = ROOT / path
    if not base.exists():
        continue
    for tf in base.rglob("*.tf"):
        text = tf.read_text(encoding="utf-8").lower()
        for forbidden in ("rekognition", "comprehend", "bedrock", "sagemaker"):
            if forbidden in text:
                fail(f"{tf.relative_to(ROOT)} activates unapproved moderation/cloud resource {forbidden!r}")

evidence = normalized("docs/evidence/sprint-12-d09-moderation-compatibility.md")
for phrase in (
    "incremental recurring implementation cost remains $0",
    "no external moderation or ai provider is activated",
    "physical-device",
    "production",
    "provider",
    "not performed",
):
    if phrase not in evidence:
        fail(f"D09 evidence is missing required boundary {phrase!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-moderation-compatibility.py" not in workflow:
    fail("CI does not enforce the Sprint 12 moderation compatibility gate")

print("Moderation compatibility gate: passed")
