import uuid

import pytest

from app.auth.security import (
    AccessTokenError,
    decode_access_token,
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
)
from app.config import Settings


def settings() -> Settings:
    return Settings(
        environment="test",
        token_signing_key="test-signing-key-with-sufficient-entropy",
        refresh_token_pepper="test-refresh-pepper-with-sufficient-entropy",
    )


def test_refresh_tokens_are_random_and_only_digests_are_persisted() -> None:
    first = new_refresh_token()
    second = new_refresh_token()
    digest = hash_refresh_token(first, settings().refresh_token_pepper.get_secret_value())

    assert first != second
    assert len(first) >= 64
    assert digest != first
    assert len(digest) == 64
    assert hash_refresh_token(first, "different-pepper") != digest


def test_access_token_round_trip_binds_account_device_and_session() -> None:
    account_id, device_id, session_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    token = issue_access_token(
        account_id=account_id,
        device_id=device_id,
        session_id=session_id,
        settings=settings(),
    )

    claims = decode_access_token(token, settings())

    assert claims["sub"] == str(account_id)
    assert claims["device_id"] == str(device_id)
    assert claims["session_id"] == str(session_id)
    assert "test-signing-key" not in token


def test_access_token_rejects_wrong_signing_key() -> None:
    token = issue_access_token(
        account_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        settings=settings(),
    )
    other = Settings(
        environment="test",
        token_signing_key="different-test-signing-key",
        refresh_token_pepper="test-refresh-pepper",
    )

    with pytest.raises(AccessTokenError):
        decode_access_token(token, other)
