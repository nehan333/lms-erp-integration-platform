"""Application configuration loaded from environment variables."""

from zoneinfo import ZoneInfo

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
    # Attendance sync uses the official mod_attendance plugin functions
    # (mod_attendance_*); Moodle has no core attendance Web Service.
    MOODLE_BASE_URL: str = ""
    MOODLE_WSTOKEN: str = ""
    MOODLE_DEFAULT_PASSWORD: str = ""
    MOODLE_TIMEOUT_SECONDS: float = 30.0
    MOODLE_DEFAULT_CATEGORY_ID: int = 1
    MOODLE_STUDENT_ROLE_ID: int = 5
    # Must match the Moodle site's own timezone setting: attendance session
    # times are created at local midnight in this zone and session dates are
    # parsed back with it, so a mismatch would shift every session by a day.
    MOODLE_SITE_TIMEZONE: str = "Asia/Kolkata"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string from the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("MOODLE_SITE_TIMEZONE")
    @classmethod
    def validate_site_timezone(cls, value: str) -> str:
        """Reject unknown IANA timezone names at startup, not mid-sync."""
        ZoneInfo(value)
        return value


settings = Settings()
