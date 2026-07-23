import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import CheckConstraint, Table

from app.db.models import Account, Device, MediaGrant


def _owned_entities() -> tuple[Account, Device]:
    account = Account(id=uuid.uuid4())
    device = Device(
        id=uuid.uuid4(),
        account=account,
        platform="ios",
        installation_id="synthetic-ptt-installation",
    )
    return account, device


def test_media_grant_is_metadata_only_and_account_device_owned() -> None:
    account, device = _owned_entities()
    now = datetime.now(UTC)
    grant = MediaGrant(
        account=account,
        device=device,
        grant_kind="receive",
        provider="livekit",
        provider_room_ref="room_opaque_1",
        provider_participant_ref="participant_opaque_1",
        action_scope="subscribe",
        policy_version="ptt-v1",
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    table = cast(Table, MediaGrant.__table__)

    assert grant in account.media_grants
    assert grant in device.media_grants
    assert next(iter(table.c.account_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.device_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.parent_grant_id.foreign_keys)).ondelete == "CASCADE"

    forbidden_fragments = {
        "token",
        "secret",
        "audio",
        "transcript",
        "coordinate",
        "latitude",
        "longitude",
        "listener",
        "callsign",
    }
    assert all(
        fragment not in column.name
        for column in table.c
        for fragment in forbidden_fragments
    )


def test_media_grant_constraints_and_indexes_fail_closed() -> None:
    table = cast(Table, MediaGrant.__table__)
    checks = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    indexes = {str(index.name): index for index in table.indexes}

    assert {
        "ck_media_grant_grant_kind_allowed",
        "ck_media_grant_provider_allowed",
        "ck_media_grant_kind_scope_consistent",
        "ck_media_grant_parent_consistent",
        "ck_media_grant_room_ref_present",
        "ck_media_grant_participant_ref_present",
        "ck_media_grant_policy_version_present",
        "ck_media_grant_expiry_after_issue",
        "ck_media_grant_revocation_after_issue",
    } <= checks
    assert set(indexes) == {
        "ix_media_grant_account_kind_expires",
        "ix_media_grant_device_id",
        "ix_media_grant_parent_grant_id",
        "ix_media_grant_provider_participant",
    }


def test_transmit_grant_references_receive_grant_without_media_content() -> None:
    account, device = _owned_entities()
    now = datetime.now(UTC)
    parent_id = uuid.uuid4()
    grant = MediaGrant(
        account=account,
        device=device,
        parent_grant_id=parent_id,
        grant_kind="transmit",
        provider="livekit",
        provider_room_ref="room_opaque_1",
        provider_participant_ref="participant_opaque_1",
        action_scope="microphone_publish",
        policy_version="ptt-v1",
        issued_at=now,
        expires_at=now + timedelta(seconds=30),
    )

    assert grant.parent_grant_id == parent_id
    assert grant.action_scope == "microphone_publish"
