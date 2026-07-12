"""
Application configuration.

Design decision:
    All configuration is sourced from environment variables (optionally via a
    local `.env` file for development). Nothing is hardcoded. We use
    `pydantic-settings` so that:
      - Types are validated at startup (fail fast, not at request time).
      - A single `Settings` object is the one source of truth, injected via
        `get_settings()` rather than reading `os.environ` scattered across
        the codebase.
      - Future phases can add new fields here (e.g. GITHUB_TOKEN,
        AWS_REGION, BEDROCK_MODEL_ID) without touching consuming code.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Every field maps 1:1 to an environment variable of the same name
    (case-insensitive). See `.env.example` for the full list with
    descriptions and example values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application identity -------------------------------------------------
    app_name: str = "AI-CI-CD-Agent"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production", "test"] = "development"

    # --- API server -------------------------------------------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Logging ------------------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # --- GitHub (Phase 2) ---------------------------------------------------------
    # Personal Access Token used to authenticate to the GitHub REST API.
    # Left blank by default so the app still boots without it; only the
    # GitHub-dependent endpoints fail (with a clear error) until it's set.
    github_token: str = ""
    github_api_base_url: str = "https://api.github.com"
    github_request_timeout_seconds: float = 10.0

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_debug(self) -> bool:
        return self.app_env in ("development", "test")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, process-wide `Settings` instance.

    `lru_cache` ensures the environment is parsed once per process rather
    than on every call, while still allowing tests to override behaviour by
    clearing the cache (`get_settings.cache_clear()`) and monkeypatching
    environment variables.
    """
    return Settings()
