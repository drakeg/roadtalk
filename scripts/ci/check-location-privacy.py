#!/usr/bin/env python3
"""Fail CI when Sprint 3 location privacy or scope boundaries regress."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"location privacy gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_tokens(path: str, tokens: tuple[str, ...]) -> None:
    content = read(path)
    for token in tokens:
        if token not in content:
            fail(f"{path} is missing required token {token!r}")


def forbid_tokens(path: str, tokens: tuple[str, ...]) -> None:
    content = read(path).lower()
    for token in tokens:
        if token.lower() in content:
            fail(f"{path} contains forbidden token {token!r}")


mobile_package = json.loads(read("mobile/package.json"))
mobile_dependencies = set(mobile_package.get("dependencies", {}))
if "expo-location" not in mobile_dependencies:
    fail("expo-location must remain pinned as the only location provider")

forbidden_mobile_dependencies = {
    "@react-native-async-storage/async-storage",
    "@sentry/react-native",
    "expo-background-fetch",
    "expo-task-manager",
    "react-native-maps",
    "@rnmapbox/maps",
    "@mapbox/mapbox-sdk",
}
unexpected_mobile = mobile_dependencies & forbidden_mobile_dependencies
if unexpected_mobile:
    fail(f"unapproved mobile dependencies: {', '.join(sorted(unexpected_mobile))}")

backend_project = tomllib.loads(read("backend/pyproject.toml"))
backend_dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0]
    for dependency in backend_project["project"]["dependencies"]
}
forbidden_backend_dependencies = {
    "boto3",
    "celery",
    "geopy",
    "googlemaps",
    "redis",
    "sentry-sdk",
}
unexpected_backend = backend_dependencies & forbidden_backend_dependencies
if unexpected_backend:
    fail(f"unapproved backend dependencies: {', '.join(sorted(unexpected_backend))}")

require_tokens(
    "mobile/app.config.ts",
    (
        '"expo-location"',
        "locationWhenInUsePermission",
        "isIosBackgroundLocationEnabled: false",
        "isAndroidBackgroundLocationEnabled: false",
    ),
)
forbid_tokens(
    "mobile/app.config.ts",
    (
        "ACCESS_BACKGROUND_LOCATION",
        "UIBackgroundModes",
        "NSLocationAlways",
        "isIosBackgroundLocationEnabled: true",
        "isAndroidBackgroundLocationEnabled: true",
        "isAndroidForegroundServiceEnabled: true",
    ),
)

location_sources = (
    "mobile/src/location/api.ts",
    "mobile/src/location/gateway.ts",
    "mobile/src/location/LocationLifecycleController.ts",
    "mobile/src/location/types.ts",
    "mobile/src/screens/LocationPermissionScreen.tsx",
)
for path in location_sources:
    forbid_tokens(
        path,
        (
            "AsyncStorage",
            "SecureStore",
            "console.",
            "analytics",
            "requestBackgroundPermissions",
            "startLocationUpdates",
            "TaskManager",
            "Geofenc",
            "react-native-maps",
            "mapbox",
            "Clipboard",
        ),
    )

require_tokens(
    "mobile/src/location/api.ts",
    ("body: JSON.stringify(sample)", '"PUT"', '"DELETE"'),
)

migration = read("backend/migrations/versions/0004_location_persistence.py").lower()
for forbidden_table in (
    "location_history",
    "location_event",
    "location_trip",
    "location_breadcrumb",
    "location_presence",
):
    if forbidden_table in migration:
        fail(f"location migration contains prohibited history/presence table {forbidden_table!r}")

require_tokens(
    "backend/app/location/schemas.py",
    (
        'ConfigDict(extra="forbid"',
        "class CurrentLocationResponse",
        "class NearbySummaryResponse",
        'Literal["none", "few", "many"]',
    ),
)

print("location privacy gate: passed")
