import pytest
from pydantic import SecretStr
from pydantic_core import ValidationError

from app.config import Settings


def test_ptt_provider_is_disabled_and_secret_free_by_default() -> None:
    settings = Settings(environment="test")

    assert settings.ptt_media_provider_enabled is False
    assert settings.ptt_media_provider == "disabled"
    assert settings.ptt_livekit_url is None
    assert settings.ptt_livekit_api_key is None
    assert settings.ptt_livekit_api_secret is None
    assert settings.ptt_transmit_grant_ttl_seconds <= settings.ptt_receive_grant_ttl_seconds


def test_disabled_ptt_rejects_stray_provider_configuration() -> None:
    with pytest.raises(ValidationError, match="must not configure"):
        Settings(environment="test", ptt_media_provider="livekit")

    with pytest.raises(ValidationError, match="must not configure"):
        Settings(environment="test", ptt_livekit_url="wss://synthetic.invalid")

    with pytest.raises(ValidationError, match="must not configure"):
        Settings(environment="test", ptt_livekit_api_key=SecretStr("synthetic-key"))

    with pytest.raises(ValidationError, match="must not configure"):
        Settings(environment="test", ptt_livekit_api_secret=SecretStr("synthetic-secret"))


def test_enabled_ptt_requires_complete_secure_livekit_configuration() -> None:
    with pytest.raises(ValidationError, match="requires URL, API key, and API secret"):
        Settings(
            environment="test",
            ptt_media_provider_enabled=True,
            ptt_media_provider="livekit",
        )

    with pytest.raises(ValidationError, match="must use wss"):
        Settings(
            environment="test",
            ptt_media_provider_enabled=True,
            ptt_media_provider="livekit",
            ptt_livekit_url="https://synthetic.invalid",
            ptt_livekit_api_key=SecretStr("synthetic-key"),
            ptt_livekit_api_secret=SecretStr("synthetic-secret"),
        )


def test_transmit_ttl_cannot_outlive_receive_grant() -> None:
    with pytest.raises(ValidationError, match="must not exceed"):
        Settings(
            environment="test",
            ptt_receive_grant_ttl_seconds=30,
            ptt_transmit_grant_ttl_seconds=60,
        )
