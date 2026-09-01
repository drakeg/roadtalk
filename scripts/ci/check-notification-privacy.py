#!/usr/bin/env python3
"""Fail CI when the Sprint 9 notification persistence boundary broadens."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Notification privacy gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return target.read_text(encoding="utf-8").lower()


models = read("backend/app/db/models.py")
notification_models = models[models.index("class notificationpreferences(") :]
notification_models = notification_models[: notification_models.index("class mediagrant(")]
for phrase in (
    "class notificationpreferences(",
    "class notification(",
    'foreignkey("account.id", ondelete="cascade")',
    'index("ix_notification_account_expires"',
    'index("ix_notification_account_issued"',
):
    if phrase not in notification_models:
        fail(f"notification persistence is missing {phrase!r}")

migration = read("backend/migrations/versions/0015_add_notifications.py")
for phrase in (
    'down_revision: str | none = "0014"',
    '"notification_preferences"',
    '"notification"',
    'ondelete="cascade"',
    'op.drop_table("notification")',
):
    if phrase not in migration:
        fail(f"notification migration is missing {phrase!r}")

api = read("backend/app/api/notifications.py")
for phrase in (
    '"/me/notification-preferences"',
    '"/me/notifications"',
    '"/me/notifications/{notification_id}/state"',
    "account_id=current.account.id",
):
    if phrase not in api:
        fail(f"notification API is missing {phrase!r}")

schemas = read("backend/app/notifications/schemas.py")
for phrase in ('extra="forbid"', 'literal["read", "dismissed"]', "expected_version"):
    if phrase not in schemas:
        fail(f"notification schema is missing {phrase!r}")
for forbidden in (
    "username",
    "password",
    "recovery_key",
    "push_token",
    "device_id",
    "installation_id",
    "provider_ref",
    "recipient_id",
    "latitude",
    "longitude",
    "coordinates",
    "route",
    "destination",
):
    if forbidden in schemas or forbidden in notification_models:
        fail(f"notification persistence/API exposes forbidden field {forbidden!r}")

service = read("backend/app/notifications/service.py")
for phrase in (
    "inbox_limit = 50",
    "notification.expires_at <= resolved_now",
    "notification.account_id == account_id",
    ".with_for_update()",
):
    if phrase not in service:
        fail(f"notification lifecycle is missing {phrase!r}")
for forbidden in ("boto3", "redis", "requests.", "httpx.", "firebase", "onesignal"):
    if forbidden in service:
        fail(f"notification service introduces forbidden dependency/call {forbidden!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-notification-privacy.py" not in workflow:
    fail("CI does not enforce the notification privacy gate")

print("Notification privacy gate: passed")
