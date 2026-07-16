from functools import lru_cache
from typing import Literal, Self

from pydantic import AliasChoices, Field, SecretStr, model_validator
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
    recovery_key_pepper: SecretStr = SecretStr("local-only-recovery-pepper-change-me")
    token_issuer: str = "roadtalk-api"
    token_audience: str = "roadtalk-mobile"
    access_token_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    refresh_token_ttl_seconds: int = Field(default=2_592_000, ge=3600)
    callsign_availability_limit: int = Field(default=30, ge=1, le=300)
    callsign_availability_window_seconds: int = Field(default=60, ge=1, le=3600)
    callsign_change_cooldown_seconds: int = Field(default=86_400, ge=0, le=2_592_000)
    recovery_attempt_limit: int = Field(default=5, ge=1, le=30)
    recovery_attempt_window_seconds: int = Field(default=900, ge=60, le=86_400)
    recovery_mutation_limit: int = Field(default=5, ge=1, le=30)
    recovery_mutation_window_seconds: int = Field(default=3_600, ge=60, le=86_400)
    location_policy_version: str = Field(default="location-v1", min_length=1, max_length=32)
    location_max_sample_age_seconds: int = Field(default=60, ge=1, le=900)
    location_max_future_seconds: int = Field(default=10, ge=0, le=120)
    location_max_usable_accuracy_m: float = Field(default=100, gt=0, le=10_000)
    location_max_retained_accuracy_m: float = Field(default=1_000, gt=0, le=50_000)
    location_max_reported_speed_mps: float = Field(default=100, gt=0, le=1_000)
    location_max_plausible_speed_mps: float = Field(default=100, gt=0, le=1_000)
    location_plausibility_slack_m: float = Field(default=250, ge=0, le=10_000)
    location_usable_ttl_seconds: int = Field(default=120, ge=10, le=3_600)
    location_degraded_ttl_seconds: int = Field(default=60, ge=10, le=3_600)
    location_cross_device_newer_seconds: int = Field(default=1, ge=0, le=60)
    location_mutation_limit: int = Field(default=30, ge=1, le=600)
    location_mutation_window_seconds: int = Field(default=60, ge=1, le=3_600)
    location_nearby_read_limit: int = Field(default=60, ge=1, le=600)
    location_nearby_read_window_seconds: int = Field(default=60, ge=1, le=3_600)

    @model_validator(mode="after")
    def validate_location_policy(self) -> Self:
        if self.location_max_usable_accuracy_m > self.location_max_retained_accuracy_m:
            raise ValueError(
                "location_max_usable_accuracy_m must not exceed location_max_retained_accuracy_m"
            )
        if self.location_degraded_ttl_seconds > self.location_usable_ttl_seconds:
            raise ValueError(
                "location_degraded_ttl_seconds must not exceed location_usable_ttl_seconds"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
