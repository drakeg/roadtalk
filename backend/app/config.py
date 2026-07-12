from functools import lru_cache
from typing import Literal

from pydantic import Field
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
