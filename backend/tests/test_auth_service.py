import asyncio
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from app.auth.security import hash_refresh_token
from app.auth.service import (
    AuthenticationError,
    revoke_session,
    rotate_refresh_token,
    token_pair,
    utcnow,
)
from app.config import Settings
from app.db.models import Session


def settings() -> Settings:
    return Settings(
        environment="test",
        token_signing_key="test-signing-key",
        refresh_token_pepper="test-refresh-pepper",
    )


def test_replayed_refresh_revokes_the_active_token_family() -> None:
    raw_token = "replayed-refresh-token-with-enough-random-looking-content"
    config = settings()
    current = Session(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        refresh_family_id=uuid.uuid4(),
        refresh_token_hash=hash_refresh_token(
            raw_token, config.refresh_token_pepper.get_secret_value()
        ),
        expires_at=utcnow() + timedelta(days=1),
        revoked_at=utcnow(),
        revoke_reason="rotated",
    )
    db = AsyncMock()
    db.scalar.return_value = current

    with pytest.raises(AuthenticationError) as raised:
        asyncio.run(rotate_refresh_token(db, raw_token, config))

    assert raised.value.code == "REFRESH_REPLAY_DETECTED"
    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()


def test_unknown_refresh_token_fails_closed() -> None:
    db = AsyncMock()
    db.scalar.return_value = None

    with pytest.raises(AuthenticationError) as raised:
        asyncio.run(rotate_refresh_token(db, "unknown-refresh-token-value-long-enough", settings()))

    assert raised.value.code == "INVALID_REFRESH_TOKEN"
    db.commit.assert_not_awaited()


def test_token_pair_binds_access_token_to_session() -> None:
    current = Session(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        refresh_family_id=uuid.uuid4(),
        refresh_token_hash="digest",
        expires_at=utcnow() + timedelta(days=1),
    )

    pair = token_pair(current, "new-refresh", settings())

    assert pair.refresh_token == "new-refresh"
    assert pair.access_token
    assert pair.expires_in == 900


def test_revoke_session_is_idempotent() -> None:
    current = Session(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        refresh_family_id=uuid.uuid4(),
        refresh_token_hash="digest",
        expires_at=utcnow() + timedelta(days=1),
    )
    db = AsyncMock()

    asyncio.run(revoke_session(db, current, "logout"))
    asyncio.run(revoke_session(db, current, "logout"))

    assert current.revoke_reason == "logout"
    db.commit.assert_awaited_once()
