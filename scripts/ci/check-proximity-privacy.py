#!/usr/bin/env python3
"""Fail CI when channel-and-proximity authorization privacy or scope regresses."""

from __future__ import annotations

import ast
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"Proximity privacy gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


module_path = "backend/app/ptt/proximity.py"
module = read(module_path)
normalized = " ".join(module.split())

required_fragments = (
    "func.ST_DWithin(CurrentLocation.position, sender_position, policy.radius_m)",
    "CurrentLocation.source_device_id == MediaGrant.device_id",
    "CurrentLocation.expires_at >= delivery_expires_at",
    "MediaGrant.expires_at >= delivery_expires_at",
    "MediaGrant.provider_room_ref == policy.room_ref",
    "MediaGrant.revoked_at.is_(None)",
    "Session.revoked_at.is_(None)",
    'Account.status == "active"',
    "MediaGrant.channel_id == policy.channel_id",
    "ChannelSelection.channel_id == MediaGrant.channel_id",
    'ChannelMembership.state == "active"',
    "Channel.provider_room_ref == policy.room_ref",
)
for fragment in required_fragments:
    if " ".join(fragment.split()) not in normalized:
        fail(f"indexed eligibility is missing {fragment!r}")

tree = ast.parse(module)
eligible_fields: set[str] = set()
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "EligibleReceiveGrant":
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                eligible_fields.add(statement.target.id)

if eligible_fields != {
    "receive_grant_id",
    "account_id",
    "device_id",
    "participant_ref",
}:
    fail("eligible result must remain the exact in-memory opaque metadata shape")

for forbidden in (
    "latitude",
    "longitude",
    "distance_m",
    "bearing",
    "callsign",
    "recipient_count",
    "listener_count",
):
    if re.search(rf"\b{forbidden}\b", module, re.I):
        fail(f"proximity module contains prohibited disclosure field {forbidden!r}")

service = read("backend/app/ptt/service.py")
service_normalized = " ".join(service.split())
for fragment in (
    "eligible_receivers = await eligibility_finder(",
    "policy=proximity_policy_from_settings(",
    '"PTT_NO_NEARBY_LISTENERS"',
    '"PTT_LOCATION_UNAVAILABLE"',
):
    if fragment not in service_normalized:
        fail(f"nearby-scoped transmit authorization is missing {fragment!r}")

eligibility_index = service_normalized.index("eligible_receivers = await eligibility_finder(")
persist_index = service_normalized.index("db.add(grant)", eligibility_index)
promotion_index = service_normalized.index("await provider.set_microphone_publish(", eligibility_index)
if not eligibility_index < persist_index < promotion_index:
    fail("eligibility must deny before transmit persistence or provider promotion")

schemas = read("backend/app/ptt/schemas.py")
if any(
    re.search(rf"\b{field}\b", schemas, re.I)
    for field in ("recipient", "listener", "distance", "radius", "coordinate")
):
    fail("PTT API schemas disclose proximity or recipient state")

for fragment in (
    "class PublicationRequest(BaseModel):",
    "track_ref: str = Field(",
    "class PublicationResponse(BaseModel):",
    'delivery_state: Literal["ready", "no_nearby_listeners", "reconciling", "ended"]',
):
    if fragment not in " ".join(schemas.split()):
        fail(f"publication API boundary is missing {fragment!r}")

publication_migration = read("backend/migrations/versions/0007_publication_metadata.py")
for column in (
    "provider_track_ref",
    "proximity_policy_version",
    "eligibility_evaluated_at",
):
    if publication_migration.count(f'\"{column}\"') < 2:
        fail(f"publication metadata migration is missing reversible column {column!r}")
for forbidden in (
    "recipient",
    "listener",
    "latitude",
    "longitude",
    "distance",
    "radius",
    "count",
    "token",
    "secret",
    "payload",
):
    if re.search(rf"\b{forbidden}\b", publication_migration, re.I):
        fail(f"publication migration contains prohibited durable field {forbidden!r}")

provider = read("backend/app/ptt/provider.py")
provider_normalized = " ".join(provider.split())
for fragment in (
    "auto_subscribe: Literal[False] = False",
    "class MicrophoneTrackLookupRequest:",
    "class VerifiedMicrophoneTrack:",
    'source: Literal["microphone"] = "microphone"',
    "active: Literal[True] = True",
    "class SelectiveSubscriptionRequest:",
    'action: Literal["subscribe", "unsubscribe"]',
    "async def verify_microphone_track(",
    "async def update_track_subscriptions(",
):
    if fragment not in provider_normalized:
        fail(f"selective-subscription provider boundary is missing {fragment!r}")

backend_project = tomllib.loads(read("backend/pyproject.toml"))
dependencies = {
    re.split(r"[<=>\[]", dependency, maxsplit=1)[0]
    for dependency in backend_project["project"]["dependencies"]
}
unexpected = dependencies & {"boto3", "celery", "livekit", "redis", "sentry-sdk"}
if unexpected:
    fail(f"unapproved dependency added: {', '.join(sorted(unexpected))}")

environment = read(".env.example")
for line in (
    "ROADTALK_PTT_PROXIMITY_POLICY_VERSION=proximity-v1",
    "ROADTALK_PTT_PROXIMITY_RADIUS_M=5000",
    "ROADTALK_PTT_MEDIA_PROVIDER_ENABLED=false",
    "ROADTALK_PTT_MEDIA_PROVIDER=disabled",
):
    if line not in environment:
        fail(f"safe server-controlled default is missing: {line}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-proximity-privacy.py" not in workflow:
    fail("CI does not enforce the proximity privacy gate")

print("Proximity privacy gate: passed")
