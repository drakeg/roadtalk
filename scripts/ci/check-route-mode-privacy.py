#!/usr/bin/env python3
"""Fail CI when the Sprint 7 route-mode boundary broadens."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Sprint 7 route-mode gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return " ".join(target.read_text(encoding="utf-8").lower().split())


schema = read("backend/app/route_mode/schemas.py")
for phrase in ('literal["nearby", "same_road"]', 'extra="forbid"', "expected_version"):
    if phrase not in schema:
        fail(f"route-mode schema is missing {phrase!r}")

service = read("backend/app/route_mode/service.py")
for phrase in ("route_mode_version_conflict", 'mode="nearby"', "with_for_update"):
    if phrase not in service:
        fail(f"route-mode service is missing {phrase!r}")

migration = read("backend/migrations/versions/0012_add_account_route_mode.py")
for phrase in ("account_route_mode", "same_road", 'down_revision: str | none = "0011"'):
    if phrase not in migration:
        fail(f"route-mode migration is missing {phrase!r}")

api = read("backend/app/api/route_mode.py")
for phrase in ('"/me/route-mode"', "current.account.id"):
    if phrase not in api:
        fail(f"route-mode API is missing {phrase!r}")

combined = " ".join((schema, service, api, migration))
for forbidden in ("osrm", "openstreetmap", "http://", "https://", "route geometry", "destination"):
    if forbidden in combined:
        fail(f"route-mode implementation contains forbidden marker {forbidden!r}")

print("Sprint 7 route-mode gate: passed")
