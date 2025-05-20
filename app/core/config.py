import os
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import field_validator  # Updated from validator

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
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }

settings = Settings()