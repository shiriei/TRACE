from typing import List, Union
from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """TRACE Core Application Settings."""

    PROJECT_NAME: str = "TRACE"
    VERSION: str = "0.2.0"
    API_V1_PREFIX: str = "/api/v1"
    DESCRIPTION: str = "TRACE — Local-First Physical Exploration System"

    # Runtime Environment
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # LM Studio Local AI Configuration
    LM_STUDIO_BASE_URL: str = Field(
        default="http://127.0.0.1:1234/v1",
        validation_alias=AliasChoices("LM_STUDIO_BASE_URL", "TRACE_LM_STUDIO_BASE_URL"),
        description="Base URL for local LM Studio OpenAI-compatible endpoint",
    )
    LM_STUDIO_MODEL: str = Field(
        default="google/gemma-3-4b",
        validation_alias=AliasChoices("LM_STUDIO_MODEL", "TRACE_LM_STUDIO_MODEL"),
        description="Configured model identifier loaded in LM Studio",
    )
    LM_STUDIO_API_KEY: str = Field(
        default="lm-studio",
        validation_alias=AliasChoices("LM_STUDIO_API_KEY", "TRACE_LM_STUDIO_API_KEY"),
        description="API key for LM Studio (local placeholder)",
    )
    LM_STUDIO_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        validation_alias=AliasChoices("LM_STUDIO_TIMEOUT_SECONDS", "TRACE_LM_STUDIO_TIMEOUT_SECONDS"),
        description="Timeout in seconds for local AI model inference",
    )

    # Persistence Configuration
    DATABASE_PATH: str = Field(
        default="runtime/traces.db",
        validation_alias=AliasChoices("DATABASE_PATH", "TRACE_DATABASE_PATH"),
        description="Path to local SQLite database file",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("LM_STUDIO_BASE_URL", mode="before")
    @classmethod
    def clean_base_url(cls, v: str) -> str:
        if isinstance(v, str):
            return v.rstrip("/")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TRACE_",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
