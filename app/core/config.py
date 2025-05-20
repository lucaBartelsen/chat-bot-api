# File: app/core/config.py (updated)
# Path: fanfix-api/app/core/config.py

import os
from typing import List
from pydantic_settings import BaseSettings

def get_cors_origins() -> List[str]:
    cors_origins_str = os.getenv("CORS_ORIGINS", "https://chatsassistant.com,https://*.chatsassistant.com")
    return [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChatAssist API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-jwt-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "1440"))  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/chat_assistant_db")
    
    # CORS
    CORS_ORIGINS: List[str] = get_cors_origins()
    
    # Domain
    DOMAIN: str = os.getenv("DOMAIN", "chatsassistant.com")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
    
    # Rate limiting
    RATE_LIMIT_MAX: int = int(os.getenv("RATE_LIMIT_MAX", "100"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "15"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()