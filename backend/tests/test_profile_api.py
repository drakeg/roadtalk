import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.db.models import Profile
from app.identity.schemas import ProfileUpdateRequest, PublicIdentity
from app.identity.service import ProfileMutationError, profile_response, update_profile


def test_public_identity_contract_contains_only_public_fields() -> None:
    identity = PublicIdentity(callsign="Road-Runner", avatar_id="classic-radio")

    assert identity.model_dump() == {
        "callsign": "Road-Runner",
        "avatar_id": "classic-radio",
    }


def test_missing_profile_is_private_and_conditionally_creatable() -> None:
    response = profile_response(None)

    assert response.model_dump() == {
        "identity": {"callsign": None, "avatar_id": None},
        "setup_completed": False,
        "version": 0,
    }


def test_profile_update_rejects_overposted_security_and_ownership_fields() -> None:
    with pytest.raises(ValidationError):
        ProfileUpdateRequest.model_validate(
            {
                "version": 0,
                "callsign": "Road-Runner",
                "account_id": str(uuid.uuid4()),
                "recovery_key": "must-not-be-accepted",
            }
        )


def test_invalid_profile_update_does_not_query_database() -> None:
    db = AsyncMock()

    with pytest.raises(ProfileMutationError) as raised:
        asyncio.run(
            update_profile(
                db,
                account_id=uuid.uuid4(),
                candidate="not valid",
                expected_version=0,
                cooldown_seconds=86_400,
            )
        )

    assert raised.value.code == "CALLSIGN_INVALID_CHARACTERS"
    db.scalar.assert_not_awaited()


def test_stale_update_fails_before_mutation() -> None:
    db = AsyncMock()
    profile = Profile(
        account_id=uuid.uuid4(),
        normalized_callsign="road-runner",
        display_callsign="Road-Runner",
        version=3,
    )
    db.scalar.return_value = profile

    with pytest.raises(ProfileMutationError) as raised:
        asyncio.run(
            update_profile(
                db,
                account_id=profile.account_id,
                candidate="Night-Owl",
                expected_version=2,
                cooldown_seconds=86_400,
            )
        )

    assert raised.value.code == "PROFILE_VERSION_CONFLICT"
    assert profile.normalized_callsign == "road-runner"
    db.commit.assert_not_awaited()


def test_callsign_change_cooldown_returns_retry_boundary() -> None:
    db = AsyncMock()
    profile = Profile(
        account_id=uuid.uuid4(),
        normalized_callsign="road-runner",
        display_callsign="Road-Runner",
        version=1,
        callsign_changed_at=datetime(2026, 7, 13, 12, 0, 0),
    )
    db.scalar.return_value = profile

    with pytest.raises(ProfileMutationError) as raised:
        asyncio.run(
            update_profile(
                db,
                account_id=profile.account_id,
                candidate="Night-Owl",
                expected_version=1,
                cooldown_seconds=3_600,
                now=datetime(2026, 7, 13, 12, 30, 0),
            )
        )

    assert raised.value.code == "CALLSIGN_CHANGE_COOLDOWN"
    assert raised.value.retry_after == 1_801
    db.commit.assert_not_awaited()
