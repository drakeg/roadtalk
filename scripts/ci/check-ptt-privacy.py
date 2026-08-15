#!/usr/bin/env python3
"""Fail CI when Sprint 4 PTT security, privacy, cost, or scope regresses."""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"PTT privacy gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def forbid_tokens(path: str, tokens: tuple[str, ...]) -> None:
    content = read(path).lower()
    for token in tokens:
        if token.lower() in content:
            fail(f"{path} contains forbidden token {token!r}")


mobile_package = json.loads(read("mobile/package.json"))
mobile_dependencies = set(mobile_package.get("dependencies", {}))
required_mobile = {
    "@livekit/react-native",
    "@livekit/react-native-expo-plugin",
    "@livekit/react-native-webrtc",
    "expo-audio",
    "livekit-client",
}
if not required_mobile <= mobile_dependencies:
    fail("approved pinned mobile media dependencies are incomplete")

forbidden_mobile = {
    "@livekit/components-react",
    "@react-native-async-storage/async-storage",
    "@sentry/react-native",
    "expo-av",
    "expo-background-fetch",
    "expo-camera",
    "expo-file-system",
    "expo-notifications",
    "expo-task-manager",
}
unexpected_mobile = mobile_dependencies & forbidden_mobile
if unexpected_mobile:
    fail(f"unapproved mobile dependencies: {', '.join(sorted(unexpected_mobile))}")

backend_project = tomllib.loads(read("backend/pyproject.toml"))
backend_dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0]
    for dependency in backend_project["project"]["dependencies"]
}
forbidden_backend = {
    "boto3",
    "celery",
    "livekit",
    "redis",
    "sentry-sdk",
}
unexpected_backend = backend_dependencies & forbidden_backend
if unexpected_backend:
    fail(f"unapproved backend dependencies: {', '.join(sorted(unexpected_backend))}")

for path in (
    "backend/app/ptt/provider.py",
    "backend/app/ptt/service.py",
    "backend/app/api/ptt.py",
):
    forbid_tokens(
        path,
        (
            "import aiohttp",
            "import httpx",
            "import requests",
            "import socket",
            "from aiohttp",
            "from httpx",
            "from requests",
            "from urllib.request",
            "EgressClient",
            "IngressClient",
            "RoomCompositeEgress",
            "start_recording",
        ),
    )

for path in (
    "mobile/src/media/api.ts",
    "mobile/src/media/liveKitRoom.ts",
    "mobile/src/media/MediaLifecycleController.ts",
    "mobile/src/media/types.ts",
):
    forbid_tokens(
        path,
        (
            "AsyncStorage",
            "SecureStore",
            "FileSystem",
            "console.",
            "setCameraEnabled",
            "startRecording",
            "startScreenShare",
            "transcription",
        ),
    )

forbid_tokens(
    "mobile/app.config.ts",
    (
        "enableBackgroundRecording: true",
        "enableBackgroundPlayback: true",
        "enableScreenShareService: true",
        "enableMultitaskingCameraAccess: true",
        "UIBackgroundModes",
    ),
)

for path in (
    "backend/app/api/ptt.py",
    "backend/app/ptt/schemas.py",
):
    forbid_tokens(
        path,
        (
            "callsign",
            "channel_id",
            "latitude",
            "longitude",
            "nearby_radius",
            "distance",
            "bearing",
            "recipient_refs",
        ),
    )

# Sprint 6 authorizes server-only channel IDs for grant binding and same-channel
# proximity decisions. They remain forbidden in client request/response schemas.
forbid_tokens(
    "backend/app/ptt/service.py",
    (
        "callsign",
        "latitude",
        "longitude",
        "nearby_radius",
    ),
)

config_sources = [ROOT / ".env.example"]
config_sources.extend((ROOT / ".github/workflows").glob("*.y*ml"))
for path in config_sources:
    content = path.read_text(encoding="utf-8")
    for variable in (
        "ROADTALK_PTT_LIVEKIT_URL",
        "ROADTALK_PTT_LIVEKIT_API_KEY",
        "ROADTALK_PTT_LIVEKIT_API_SECRET",
    ):
        if re.search(rf"(?m)^\s*{variable}\s*[:=]", content):
            fail(f"{path.relative_to(ROOT)} configures prohibited live provider value {variable}")
    if re.search(r"(?m)^\s*ROADTALK_PTT_MEDIA_PROVIDER_ENABLED\s*[:=]\s*['\"]?true", content, re.I):
        fail(f"{path.relative_to(ROOT)} enables the live media provider")

model_tree = ast.parse(read("backend/app/db/models.py"))
media_columns: set[str] = set()
for node in model_tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "MediaGrant":
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                media_columns.add(statement.target.id)

forbidden_column_fragments = {
    "audio",
    "callsign",
    "coordinate",
    "latitude",
    "listener",
    "longitude",
    "secret",
    "token",
    "transcript",
}
for column in media_columns:
    if any(fragment in column.lower() for fragment in forbidden_column_fragments):
        fail(f"media_grant contains prohibited durable column {column!r}")

for migration_path in (
    "backend/migrations/versions/0005_media_grant.py",
    "backend/migrations/versions/0006_receive_grant_idempotency.py",
    "backend/migrations/versions/0007_publication_metadata.py",
):
    migration_tree = ast.parse(read(migration_path))
    for node in ast.walk(migration_tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "Column"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            column = node.args[0].value
            if any(fragment in column.lower() for fragment in forbidden_column_fragments):
                fail(f"{migration_path} contains prohibited durable column {column!r}")

logging_tree = ast.parse(read("backend/app/logging.py"))
allowed_log_fields: set[str] = set()
for node in ast.walk(logging_tree):
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "_allowed_fields" for target in node.targets
    ):
        if isinstance(node.value, ast.Set):
            allowed_log_fields = {
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            }

for field in allowed_log_fields:
    if any(fragment in field.lower() for fragment in forbidden_column_fragments):
        fail(f"structured logging allowlist contains sensitive field {field!r}")

for evidence in (ROOT / "docs/evidence").rglob("*"):
    if not evidence.is_file():
        continue
    if evidence.suffix.lower() in {
        ".aac",
        ".flac",
        ".m4a",
        ".mp3",
        ".ogg",
        ".opus",
        ".pcm",
        ".wav",
    }:
        fail(f"evidence contains prohibited audio file {evidence.relative_to(ROOT)}")
    if evidence.suffix.lower() not in {".md", ".json", ".txt", ".yaml", ".yml"}:
        continue
    content = evidence.read_text(encoding="utf-8", errors="replace")
    if re.search(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", content):
        fail(f"evidence contains a JWT-shaped token in {evidence.relative_to(ROOT)}")
    if "-----BEGIN PRIVATE KEY-----" in content:
        fail(f"evidence contains a private key in {evidence.relative_to(ROOT)}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-ptt-privacy.py" not in workflow:
    fail("CI does not enforce the Sprint 4 PTT privacy gate")

print("PTT privacy gate: passed")
