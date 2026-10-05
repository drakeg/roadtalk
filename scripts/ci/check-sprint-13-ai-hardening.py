#!/usr/bin/env python3
"""Fail CI if Sprint 13 AI privacy, provider, reliability, or cost boundaries regress."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 13 AI hardening gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return target.read_text(encoding="utf-8")


implementation_paths = (
    "backend/app/ai/contracts.py",
    "backend/app/ai/provider.py",
    "backend/app/ai/transcription.py",
    "backend/app/ai/summary.py",
    "backend/app/ai/translation.py",
    "browser/ai-controls.js",
    "mobile/src/ai/types.ts",
    "mobile/src/ai/MobileAiController.ts",
    "mobile/src/screens/AiToolsScreen.tsx",
)
implementation = "\n".join(read(path).lower() for path in implementation_paths)

for forbidden in (
    "openai",
    "anthropic",
    "botocore",
    "boto3",
    "bedrock",
    "sagemaker",
    "vertexai",
    "google.generativeai",
    "azure.ai",
    "urllib.request",
    "fetch(",
    "xmlhttprequest",
    "eventsource(",
):
    if forbidden in implementation:
        fail(f"AI implementation references unapproved external/network capability {forbidden!r}")

for pattern in (
    r"(^|\\n)\\s*(from|import)\\s+requests\\b",
    r"(^|\\n)\\s*(from|import)\\s+httpx\\b",
    r"(^|\\n)\\s*(from|import)\\s+aiohttp\\b",
):
    if re.search(pattern, implementation):
        fail(f"AI implementation imports an unapproved network client matching {pattern!r}")

provider = read("backend/app/ai/provider.py")
for required in (
    "AI_PROVIDER_MAX_CONCURRENT_REQUESTS",
    "AI_PROVIDER_REPLAY_WINDOW",
    "_active_request_ids",
    "_completed_request_ids",
    'raise AiProviderUnavailable("AI provider unavailable")',
):
    if required not in provider:
        fail(f"provider hardening is missing {required!r}")

for path, required_tests in {
    "backend/tests/test_ai_provider.py": (
        "test_boundary_rejects_completed_request_replay",
        "test_boundary_rejects_concurrent_duplicate_request_id",
        "test_boundary_enforces_bounded_concurrency",
        "test_injection_like_text_is_treated_as_bounded_content",
    ),
    "backend/tests/test_ai_transcription.py": (
        "test_transcription_fails_closed_without_active_transmit_grant",
        "test_ephemeral_audio_bound_is_enforced_before_provider_processing",
    ),
    "backend/tests/test_ai_summary.py": (
        "test_stale_source_fails_closed_before_provider_call",
        "test_provider_output_larger_than_requested_bound_is_rejected",
    ),
    "backend/tests/test_ai_translation.py": (
        "test_stale_source_fails_closed_before_provider_call",
        "test_provider_output_larger_than_requested_bound_is_rejected",
    ),
    "backend/tests/test_browser_ai_experience.py": (
        "test_browser_ai_has_no_automatic_network_or_provider_activation",
        "test_browser_ai_clears_stale_results_for_offline_or_disabled_state",
    ),
    "backend/tests/test_mobile_ai_experience.py": (
        "test_mobile_ai_requires_explicit_foreground_actions",
        "test_mobile_ai_degraded_states_clear_stale_results",
    ),
}.items():
    content = read(path)
    for name in required_tests:
        if name not in content:
            fail(f"{path} is missing required Sprint 13 hardening coverage {name!r}")

backend = tomllib.loads(read("backend/pyproject.toml"))
backend_dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0].lower()
    for dependency in backend["project"]["dependencies"]
}
mobile_dependencies = set(json.loads(read("mobile/package.json"))["dependencies"])
for forbidden in (
    "boto3",
    "botocore",
    "openai",
    "anthropic",
    "google-generativeai",
    "google-cloud-aiplatform",
    "azure-ai-inference",
    "@aws-sdk/client-bedrock-runtime",
):
    if forbidden in backend_dependencies or forbidden in mobile_dependencies:
        fail(f"unapproved AI/cloud dependency detected: {forbidden}")

for base_path in (
    "infrastructure/bootstrap",
    "infrastructure/environments",
    "infrastructure/modules",
):
    base = ROOT / base_path
    if not base.exists():
        continue
    for tf in base.rglob("*.tf"):
        content = tf.read_text(encoding="utf-8").lower()
        for forbidden in (
            "bedrock",
            "sagemaker",
            "aws_transcribe",
            "aws_translate",
            "comprehend",
            "rekognition",
        ):
            if forbidden in content:
                fail(
                    f"{tf.relative_to(ROOT)} activates unapproved AI/cloud resource "
                    f"{forbidden!r}"
                )

compose = read("compose.yaml").lower()
for forbidden in (
    "roadtalk_ai_provider",
    "openai_api_key",
    "anthropic_api_key",
    "bedrock",
    "sagemaker",
):
    if forbidden in compose:
        fail(f"Compose activates unapproved AI/provider configuration {forbidden!r}")

evidence = " ".join(
    read("docs/evidence/sprint-13-d09-ai-hardening.md").lower().split()
)
for phrase in (
    "incremental recurring implementation cost remains $0",
    "no external ai or speech provider is activated",
    "physical-device",
    "live-provider",
    "production",
    "not performed",
):
    if phrase not in evidence:
        fail(f"D09 evidence is missing required boundary {phrase!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-sprint-13-ai-hardening.py" not in workflow:
    fail("CI does not enforce the Sprint 13 AI hardening gate")

print("Sprint 13 AI hardening gate: passed")
