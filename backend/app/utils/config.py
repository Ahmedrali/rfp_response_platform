import logging
from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RFP Platform API"
    PROJECT_VERSION: str = "0.1.0" # Added
    API_V1_STR: str = "/api/v1"

    # Database settings
    # Example: postgresql+asyncpg://user:password@host:port/db_name
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rfp_platform"

    # CORS settings
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:8080"] # Renamed from CORS_ORIGINS

    # Logging settings
    LOG_LEVEL: str = "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # For SQLAlchemy echo
    ECHO_SQL: bool = False

    # Server settings
    SERVER_HOST: str = "0.0.0.0" # Added
    SERVER_PORT: int = 8000 # Added
    RELOAD_APP: bool = True # Added for development

    # OpenAI settings (from .env.example)
    OPENAI_API_KEY: str = "your_openai_api_key_here"
    OPENAI_BASE_URL: str = "https://optogpt.optomatica.com/api"
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    CHAT_MODEL: str = "deepseek.deepseek-chat"

    # Redis settings (from .env.example)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Secret key (from .env.example)
    SECRET_KEY: str = "your_secret_key_here"

    # Tokenizers parallelism (from .env.example)
    TOKENIZERS_PARALLELISM: bool = False


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    def __init__(self, **values):
        super().__init__(**values)
        # Ensure BACKEND_CORS_ORIGINS is a list of strings
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            self.BACKEND_CORS_ORIGINS = [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        
        if self.LOG_LEVEL.upper() == "DEBUG":
            self.ECHO_SQL = True


settings = Settings()

# Configure root logger based on LOG_LEVEL from settings
# This basicConfig might conflict if structlog is also configuring the root logger.
# Typically, structlog handles the root logger configuration.
# For now, let's keep it as it was in your original file.
logging.basicConfig(level=settings.LOG_LEVEL.upper())
