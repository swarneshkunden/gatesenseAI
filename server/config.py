import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    port: int = Field(default=8000, validation_alias="PORT")
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Rate Limits (requests per minute)
    rate_limit_strict: int = Field(default=5, validation_alias="RATE_LIMIT_STRICT")
    rate_limit_default: int = Field(default=60, validation_alias="RATE_LIMIT_DEFAULT")
    rate_limit_loose: int = Field(default=200, validation_alias="RATE_LIMIT_LOOSE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
