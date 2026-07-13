from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ROADTALK_",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "RoadTalk API"
    environment: Literal["local", "test", "field-test", "production"] = "local"
    version: str = "0.1.0"
    log_level: str = "INFO"
    docs_enabled: bool = True
    trusted_request_id_max_length: int = Field(default=128, ge=16, le=256)
    database_url: SecretStr = Field(
        default=SecretStr(
            "postgresql+psycopg://roadtalk:roadtalk_local_only_change_me@localhost:5432/roadtalk"
        ),
        validation_alias=AliasChoices("ROADTALK_DATABASE_URL", "DATABASE_URL"),
    )
    database_echo: bool = False
    database_check_enabled: bool = True
    token_signing_key: SecretStr = SecretStr("local-only-signing-key-change-me")
    refresh_token_pepper: SecretStr = SecretStr("local-only-refresh-pepper-change-me")
    token_issuer: str = "roadtalk-api"
    token_audience: str = "roadtalk-mobile"
    access_token_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    refresh_token_ttl_seconds: int = Field(default=2_592_000, ge=3600)
    callsign_availability_limit: int = Field(default=30, ge=1, le=300)
    callsign_availability_window_seconds: int = Field(default=60, ge=1, le=3600)


@lru_cache
def get_settings() -> Settings:
    return Settings()
