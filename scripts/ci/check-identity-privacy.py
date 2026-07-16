#!/usr/bin/env python3
"""Fail CI when Sprint 2 privacy and scope boundaries regress."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"identity privacy gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def dependency_names(path: Path, group: str) -> set[str]:
    package = json.loads(path.read_text(encoding="utf-8"))
    values = package.get(group, {})
    return set(values) if isinstance(values, dict) else set()


def require_absent(path: Path, values: tuple[str, ...]) -> None:
    content = path.read_text(encoding="utf-8")
    for value in values:
        if value in content:
            fail(f"{path.relative_to(ROOT)} contains forbidden token {value!r}")


mobile_dependencies = dependency_names(ROOT / "mobile/package.json", "dependencies")
forbidden_mobile_dependencies = {
    "@aws-sdk/client-s3",
    "@react-native-async-storage/async-storage",
    "expo-audio",
    "expo-av",
    "expo-camera",
    "expo-image-picker",
    "expo-notifications",
}
unexpected = mobile_dependencies & forbidden_mobile_dependencies
if unexpected:
    fail(f"unapproved mobile dependencies: {', '.join(sorted(unexpected))}")

backend_project = tomllib.loads((ROOT / "backend/pyproject.toml").read_text(encoding="utf-8"))
backend_dependencies = {
    dependency.split("[", 1)[0].split("<", 1)[0].split(">", 1)[0].split("=", 1)[0]
    for dependency in backend_project["project"]["dependencies"]
}
forbidden_backend_dependencies = {
    "boto3",
    "redis",
    "sendgrid",
    "twilio",
}
unexpected = backend_dependencies & forbidden_backend_dependencies
if unexpected:
    fail(f"unapproved backend dependencies: {', '.join(sorted(unexpected))}")

recovery_sources = (
    ROOT / "mobile/src/recovery/api.ts",
    ROOT / "mobile/src/recovery/storage.ts",
    ROOT / "mobile/src/screens/RecoveryScreen.tsx",
)
for source in recovery_sources:
    require_absent(
        source,
        (
            "AsyncStorage",
            "Clipboard",
            "Linking.openURL",
            "console.debug",
            "console.error",
            "console.info",
            "console.log",
            "console.warn",
        ),
    )

app_config = ROOT / "mobile/app.config.ts"
require_absent(
    app_config,
    (
        "NSCameraUsageDescription",
        "NSLocation",
        "NSMicrophoneUsageDescription",
        "android.permission.ACCESS_",
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
    ),
)

middleware = ROOT / "backend/app/middleware.py"
require_absent(middleware, ("request.url.path", '"path":'))

logging_source = (ROOT / "backend/app/logging.py").read_text(encoding="utf-8")
for required in (
    "_allowed_events",
    "_allowed_fields",
    '"problem_code"',
    '"result_class"',
    '"route"',
    '"status_code"',
):
    if required not in logging_source:
        fail(f"backend/app/logging.py is missing {required!r}")

print("identity privacy gate: passed")
