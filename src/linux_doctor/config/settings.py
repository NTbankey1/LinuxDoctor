"""Configuration settings for the application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    # General
    debug: bool = False
    log_level: str = "INFO"

    # Paths
    kb_path: str = "data/kb"
    db_path: str = "data/sessions.sqlite"

    # Shell Execution
    shell_timeout_seconds: int = 10
    forbidden_commands: list[str] = ["sudo", "rm", "mkfs", "dd", "chmod", "chown"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
