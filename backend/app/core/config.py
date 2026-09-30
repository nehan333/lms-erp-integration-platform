"""Application configuration loaded from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings backed by environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "LMS-ERP Integration Platform"
    PROJECT_DESCRIPTION: str = (
        "Backend API for the College ERP with Moodle LMS integration."
    )
    PROJECT_VERSION: str = "0.1.0"

    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/lms_erp"
    )

    CORS_ORIGINS: list[str] = ["*"]

    # Moodle Web Services integration (Sprint 7)
    MOODLE_BASE_URL: str = ""
    MOODLE_WSTOKEN: str = ""
    MOODLE_DEFAULT_PASSWORD: str = ""
    MOODLE_TIMEOUT_SECONDS: float = 30.0
    MOODLE_DEFAULT_CATEGORY_ID: int = 1
    MOODLE_STUDENT_ROLE_ID: int = 5
    MOODLE_ATTENDANCE_WSFUNCTION: str = "mod_attendance_add_take"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string from the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
