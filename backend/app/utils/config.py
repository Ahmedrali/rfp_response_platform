import logging
from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RFP Platform API"
    API_V1_STR: str = "/api/v1"

    # Database settings
    # Example: postgresql+asyncpg://user:password@host:port/db_name
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rfp_platform"

    # Redis settings for Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS settings
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:8080", "file://"] # Comma-separated string or list

    # Logging settings
    LOG_LEVEL: str = "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # For SQLAlchemy echo
    ECHO_SQL: bool = False


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    def __init__(self, **values):
        super().__init__(**values)
        # Ensure CORS_ORIGINS is a list of strings
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        
        if self.LOG_LEVEL.upper() == "DEBUG":
            self.ECHO_SQL = True


settings = Settings()

# Configure root logger based on LOG_LEVEL from settings
logging.basicConfig(level=settings.LOG_LEVEL.upper())


def get_database_url() -> str:
    """Get the database URL from settings."""
    return settings.DATABASE_URL
