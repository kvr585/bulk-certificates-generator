from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Bulk Certificate Generator"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./certificates.db"

    # Storage
    STORAGE_BACKEND: Literal["local"] = "local"
    STORAGE_LOCAL_DIR: str = "generated_certificates"

    # Limits and constraints
    MAX_RECIPIENTS_PER_JOB: int = 1000

    @property
    def storage_path(self) -> Path:
        """Absolute Path to the local storage directory."""
        path = Path(self.STORAGE_LOCAL_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
