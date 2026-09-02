#!/usr/bin/env python3
"""Fail CI when the Sprint 9 notification persistence/authorization/provider boundary broadens."""

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

receipt_model = read("backend/app/notifications/models.py")
for phrase in (
    "class notificationdeliveryreceipt(",
    'foreignkey("account.id", ondelete="cascade")',
    'foreignkey("notification.id", ondelete="set null")',
    "idempotency_key_hash",
    "request_fingerprint",
    "guard_expires_at",
):
    if phrase not in receipt_model:
        fail(f"notification replay receipt is missing {phrase!r}")
for forbidden in (
    "sender_account",
    "sender_device",
    "recipient_id",
    "latitude",
    "longitude",
    "distance",
    "bearing",
    "heading",
    "speed",
    "route",
    "corridor",
    "destination",
    "message",
    "channel_label",
    "provider_ref",
    "push_token",
):
    if forbidden in receipt_model:
        fail(f"notification replay receipt stores forbidden field {forbidden!r}")

composition_migration = read(
    "backend/migrations/versions/0016_add_notification_delivery_receipts.py"
)
for phrase in (
    'down_revision: str | none = "0015"',
    '"notification_delivery_receipt"',
    '"idempotency_key_hash"',
    '"request_fingerprint"',
    'ondelete="set null"',
    'op.drop_table("notification_delivery_receipt")',
):
    if phrase not in composition_migration:
        fail(f"notification authorization migration is missing {phrase!r}")

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
    "eligible = await eligibility_finder(",
    "candidate_account_ids = {item.account_id for item in eligible}",
    "recipient_account_ids = await _notification_enabled_accounts(",
    "await store_notification_idempotent(",
    "notificationdeliveryreceipt.guard_expires_at <= resolved_now",
):
    if phrase not in service:
        fail(f"notification lifecycle/authorization is missing {phrase!r}")
for forbidden in ("boto3", "redis", "requests.", "httpx.", "firebase", "onesignal"):
    if forbidden in service:
        fail(f"notification service introduces forbidden dependency/call {forbidden!r}")

contracts = read("backend/app/notifications/contracts.py")
for forbidden in (
    "recipient_ids:",
    "account_ids:",
    "device_ids:",
    "latitude:",
    "longitude:",
    "radius_m:",
    "route:",
    "corridor:",
):
    if forbidden in contracts:
        fail(f"notification contract exposes targeting override {forbidden!r}")

provider = read("backend/app/notifications/provider.py")
for phrase in (
    "class disablednotificationprovider",
    "class fakenotificationprovider",
    "class notificationdeliveryboundary",
    'literal["disabled", "fake"]',
    'provider_version="fake-v1"',
    "asyncio.wait_for(",
    'environment not in {"local", "test"}',
):
    if phrase not in provider:
        fail(f"notification provider boundary is missing {phrase!r}")
for forbidden in (
    "apns",
    "firebase",
    "fcm",
    "expo",
    "sns",
    "pinpoint",
    "webpush",
    "web_push",
    "requests.",
    "httpx.",
    "boto3",
    "api_key",
    "push_token",
    "provider_url",
    "read_at",
    "responded",
):
    if forbidden in provider:
        fail(f"notification provider boundary introduces forbidden capability {forbidden!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-notification-privacy.py" not in workflow:
    fail("CI does not enforce the notification privacy gate")

print("Notification privacy gate: passed")
