#!/usr/bin/env python3
"""Fail CI if Sprint 9 notification scope gains sensitive, paid, or background capabilities."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Notification hardening gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return target.read_text(encoding="utf-8").lower()


def is_test_source(path: Path) -> bool:
    """Return True for test-only source that may name forbidden APIs in assertions."""
    if "__tests__" in path.parts:
        return True
    return any(part in {"tests", "test"} for part in path.parts) or any(
        path.name.endswith(suffix)
        for suffix in (
            ".test.py",
            ".test.ts",
            ".test.tsx",
            ".test.js",
            ".test.jsx",
            ".spec.py",
            ".spec.ts",
            ".spec.tsx",
            ".spec.js",
            ".spec.jsx",
        )
    )


notification_files = {
    path: read(path)
    for path in (
        "backend/app/api/notifications.py",
        "backend/app/notifications/contracts.py",
        "backend/app/notifications/provider.py",
        "backend/app/notifications/service.py",
        "backend/app/notifications/schemas.py",
        "backend/app/notifications/limiter.py",
        "mobile/src/notifications/api.ts",
    )
}
combined = "\n".join(notification_files.values())
credential_guard_files = {
    "backend/app/notifications/contracts.py",
    "mobile/src/notifications/api.ts",
}
credential_surface = "\n".join(
    text
    for path, text in notification_files.items()
    if path not in credential_guard_files
)

for forbidden in (
    "apns",
    "firebase",
    "fcm",
    "expo-notifications",
    "expo_notifications",
    "onesignal",
    "webpush",
    "web-push",
    "pinpoint",
    "notification hub",
    "pushwoosh",
    "pusher beams",
    "braze",
    "airship",
):
    if forbidden in combined:
        fail(f"notification implementation references external push capability {forbidden!r}")

for forbidden in (
    "api_key",
    "apikey",
    "server_key",
    "private_key",
    "provider_token",
    "push_token",
    "device_token",
    "registration_token",
    "credentials_json",
):
    if forbidden in credential_surface:
        fail(f"notification implementation references provider credential/token field {forbidden!r}")

for forbidden in (
    "requests.",
    "httpx.",
    "aiohttp.",
    "urllib.request",
    "boto3",
    "botocore",
):
    if forbidden in credential_surface:
        fail(f"notification implementation adds external network/provider client {forbidden!r}")

contracts = notification_files["backend/app/notifications/contracts.py"]
for forbidden in (
    "recipient_ids",
    "latitude",
    "longitude",
    "coordinates",
    "radius_m",
    "distance_m",
    "route",
    "corridor",
    "destination",
    "access_token",
    "refresh_token",
    "password",
    "recovery_key",
):
    if forbidden not in contracts:
        fail(f"notification prohibited-field contract no longer names {forbidden!r}")

mobile_api = notification_files["mobile/src/notifications/api.ts"]
for forbidden in (
    "push_token",
    "provider",
    "provider_ref",
    "provider_token",
    "access_token",
    "refresh_token",
    "password",
    "recovery_key",
):
    if forbidden not in mobile_api:
        fail(f"mobile notification response guard no longer rejects {forbidden!r}")

api = notification_files["backend/app/api/notifications.py"]
for pattern in (
    r"logger\.(?:debug|info|warning|error|exception).*payload",
    r"print\(.*payload",
    r"logger\.(?:debug|info|warning|error|exception).*idempotency",
    r"print\(.*idempotency",
):
    if re.search(pattern, api):
        fail("notification API logs sensitive payload/idempotency material")

mobile_manifest = read("mobile/package.json")
for forbidden_dependency in (
    "expo-notifications",
    "@react-native-firebase/messaging",
    "@notifee/react-native",
    "react-native-onesignal",
    "@aws-sdk/client-sns",
    "@aws-sdk/client-pinpoint",
):
    if forbidden_dependency in mobile_manifest:
        fail(f"mobile dependencies activate push/provider SDK {forbidden_dependency!r}")

pyproject = read("backend/pyproject.toml")
for forbidden_dependency in (
    "boto3",
    "firebase-admin",
    "pyfcm",
    "apns2",
    "pywebpush",
    "onesignal-sdk",
):
    if forbidden_dependency in pyproject:
        fail(f"backend dependencies activate push/provider SDK {forbidden_dependency!r}")

for path in ("mobile/app.json", "mobile/app.config.ts", "mobile/app.config.js"):
    target = ROOT / path
    if not target.is_file():
        continue
    config = target.read_text(encoding="utf-8").lower()
    for forbidden in (
        "access_background_location",
        "location_always",
        "locationalwaysandwheninuseusagedescription",
        "uibackgroundmodes",
        '"audio"',
        "background-fetch",
        "remote-notification",
    ):
        if forbidden in config:
            fail(f"mobile config activates forbidden background capability {forbidden!r}")

for path in ("mobile/src", "backend/app/notifications"):
    base = ROOT / path
    if not base.exists():
        continue
    for source in base.rglob("*"):
        if source.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            continue
        if is_test_source(source.relative_to(ROOT)):
            continue
        text = source.read_text(encoding="utf-8").lower()
        for forbidden in (
            "startlocationupdatesasync",
            "startlocationupdates",
            "segment.com",
            "mixpanel",
            "amplitude",
        ):
            if forbidden in text:
                fail(f"{source.relative_to(ROOT)} activates forbidden capability {forbidden!r}")

workflow = read(".github/workflows/ci.yml")
for required in (
    "python scripts/ci/check-notification-hardening.py",
    "pytest -q -s tests/test_notification_scale.py",
):
    if required not in workflow:
        fail(f"CI does not enforce D09 gate {required!r}")

print("Notification hardening gate: passed")
