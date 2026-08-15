#!/usr/bin/env python3
"""Fail CI when the S06-D02 channel catalog or selection boundary drifts."""

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

api = read("backend/app/api/channels.py")
for phrase in (
    '@router.get("/channels"',
    '@router.get("/me/channel"',
    '@router.post("/channels/{channel_id}/select"',
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
    "invite",
):
    if forbidden in schemas:
        fail(f"channel response schema exposes forbidden field {forbidden!r}")

service = read("backend/app/channels/service.py")
for phrase in (
    'channelmembership.state == "active"',
    'channel.channel_type == "public"',
    ".with_for_update()",
    "selection.channel_id = general_channel_id",
    '"channel_not_available"',
    '"channel_media_active"',
):
    if phrase not in service:
        fail(f"channel authorization is missing {phrase!r}")
for forbidden in ("livekit", "boto3", "redis", "requests.", "httpx."):
    if forbidden in service:
        fail(f"channel catalog introduces forbidden dependency/call {forbidden!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-channel-privacy.py" not in workflow:
    fail("CI does not enforce the channel privacy gate")

print("Channel privacy gate: passed")
