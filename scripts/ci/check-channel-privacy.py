#!/usr/bin/env python3
"""Fail CI when the S06-D03 channel and invite boundary drifts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Channel privacy gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return target.read_text(encoding="utf-8").lower()


models = read("backend/app/db/models.py")
for phrase in (
    "class channel(",
    "class channelmembership(",
    "class channelselection(",
    "channel_type in ('public', 'private')",
    'foreignkey("channel.id", ondelete="restrict")',
    'index("ix_media_grant_channel_id", "channel_id")',
):
    if phrase not in models:
        fail(f"channel persistence is missing {phrase!r}")

migration = read("backend/migrations/versions/0008_channel_catalog.py")
for phrase in (
    'general_channel_id = uuid.uuid("00000000-0000-4000-8000-000000000001")',
    'rv_channel_id = uuid.uuid("00000000-0000-4000-8000-000000000002")',
    '"stable_slug": "general"',
    '"stable_slug": "rv"',
    "insert into channel_selection",
    "update media_grant set channel_id",
    'op.alter_column("media_grant", "channel_id", nullable=false)',
):
    if phrase not in migration:
        fail(f"channel migration is missing {phrase!r}")

invite_migration = read("backend/migrations/versions/0009_private_channel_invites.py")
for phrase in (
    '"channel_invite"',
    'sa.column("secret_hash"',
    'sa.column("fingerprint"',
    'sa.column("rotation_idempotency_hash"',
):
    if phrase not in invite_migration:
        fail(f"invite migration is missing {phrase!r}")

api = read("backend/app/api/channels.py")
for phrase in (
    '@router.get("/channels"',
    '@router.get("/me/channel"',
    '@router.post("/channels/{channel_id}/select"',
    '"/channels/private"',
    '@router.post("/channels/private/join"',
    '@router.delete("/channels/{channel_id}/membership"',
    '"/channels/{channel_id}/invite/rotation"',
    '@router.delete("/channels/{channel_id}"',
    "account_id=current.account.id",
):
    if phrase not in api:
        fail(f"caller-scoped channel API is missing {phrase!r}")

schemas = read("backend/app/channels/schemas.py")
for forbidden in (
    "member_count",
    "members:",
    "owner_id",
    "creator_account_id",
    "provider_room_ref",
    "participant_ref",
):
    if forbidden in schemas:
        fail(f"channel response schema exposes forbidden field {forbidden!r}")
if schemas.count("invite: str | none") != 1:
    fail("one-time invite disclosure is not isolated to one response schema")
for forbidden in ("invite_hash", "secret_hash", "fingerprint"):
    if forbidden in schemas:
        fail(f"channel response schema exposes invite storage field {forbidden!r}")

service = read("backend/app/channels/service.py")
for phrase in (
    'channelmembership.state == "active"',
    'channel.channel_type == "public"',
    ".with_for_update()",
    "selection.channel_id = general_channel_id",
    '"channel_not_available"',
    '"channel_media_active"',
    'reason="channel_switched"',
    'reason="channel_left"',
    'reason="channel_closed"',
    "revoke_channel_media_grants(",
    "hash_invite(",
    "verify_invite(",
    '"channel_invite_invalid"',
    "rotation_idempotency_hash",
):
    if phrase not in service:
        fail(f"channel authorization is missing {phrase!r}")

media_service = read("backend/app/ptt/service.py")
for phrase in (
    '"channel_switched"',
    '"channel_left"',
    '"channel_closed"',
    "async def revoke_channel_media_grants(",
    "mediagrant.revoked_at.is_(none)",
):
    if phrase not in media_service:
        fail(f"channel reconciliation is missing {phrase!r}")
recovery_service = read("backend/app/recovery/service.py")
for phrase in (
    "channel.creator_account_id == account_id",
    "channelmembership.account_id == account_id",
    "mediagrant.account_id == account_id",
):
    if phrase not in recovery_service:
        fail(f"temporary-account deletion guard is missing {phrase!r}")

mobile_api = read("mobile/src/channels/api.ts")
for phrase in (
    '"/channels"',
    '"/me/channel"',
    '"/channels/private/join"',
    '"member_count"',
    '"provider_room_ref"',
    '"idempotency-key"',
    '"/channels/private"',
    '"closed"',
):
    if phrase not in mobile_api:
        fail(f"mobile channel transport is missing {phrase!r}")

mobile_controller = read("mobile/src/channels/ChannelController.ts")
media_controller = read("mobile/src/media/MediaLifecycleController.ts")
for phrase in ("preparechanneltransition", "completechanneltransition"):
    if phrase not in mobile_controller or phrase not in media_controller:
        fail(f"safe mobile channel transition is missing {phrase!r}")

mobile_ui = read("mobile/src/screens/ChannelScreen.tsx")
for phrase in (
    "save this invite now",
    "dismissinvite",
    "rotate invite",
    "close private channel",
    "create private channel",
):
    if phrase not in mobile_ui:
        fail(f"mobile private-channel lifecycle is missing {phrase!r}")
for forbidden in (
    "member_count",
    "owner_id",
    "provider_room_ref",
    "participant_ref",
    "fingerprint",
    "console.",
    "analytics",
    "asyncstorage",
    "securestore",
):
    if forbidden in mobile_ui or forbidden in mobile_controller:
        fail(f"mobile channel experience exposes forbidden field/path {forbidden!r}")
for forbidden in ("livekit", "boto3", "redis", "requests.", "httpx."):
    if forbidden in service:
        fail(f"channel catalog introduces forbidden dependency/call {forbidden!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-channel-privacy.py" not in workflow:
    fail("CI does not enforce the channel privacy gate")

print("Channel privacy gate: passed")
