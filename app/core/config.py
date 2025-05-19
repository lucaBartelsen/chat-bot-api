# File: app/core/config.py (updated)
# Path: fanfix-api/app/core/config.py

import os
from typing import List
# Change pydantic_settings to pydantic
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FanFix ChatAssist API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-jwt-secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fanfix_db")
    CORS_ORIGINS: List[str] = ["*"]  # Configure appropriately for production
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    
    class Config:
        env_file = ".env"

settings = Settings()