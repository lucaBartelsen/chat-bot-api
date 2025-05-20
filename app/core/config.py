import os
import json
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "FanFix ChatAssist API"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "your-secret-key-for-development")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fanfix"
    )
    SYNC_DATABASE_URL: str = os.environ.get(
        "SYNC_DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/fanfix"
    )
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")
    DEFAULT_MODEL: str = "gpt-4"
    SUGGESTION_COUNT: int = 3
    
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
        json_schema_extra={
            "examples": {
                "CORS_ORIGINS": ["http://localhost:3000", "https://chatassistant.com"]
            }
        }
    )
    
    # Custom validator for CORS_ORIGINS to handle JSON array strings
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                # Only accept JSON array format
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError(
                    "CORS_ORIGINS must be a valid JSON array string, e.g., "
                    '["http://localhost:3000", "https://chatassistant.com"]'
                )
        return v

settings = Settings()