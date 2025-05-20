# File: app/core/config.py (fixed)
# Path: fanfix-api/app/core/config.py

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChatAssist API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-jwt-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "1440"))  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/chat_assistant_db")
    
    # CORS - Default value directly, not from env
    CORS_ORIGINS: Optional[List[str]] = None
    
    # Domain
    DOMAIN: str = os.getenv("DOMAIN", "chatsassistant.com")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
    
    # Rate limiting
    RATE_LIMIT_MAX: int = int(os.getenv("RATE_LIMIT_MAX", "100"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "15"))
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
    
    def model_post_init(self, __context):
        # Process CORS_ORIGINS from environment variable after Pydantic initialization
        cors_origins_str = os.getenv("CORS_ORIGINS", "https://chatsassistant.com,https://*.chatsassistant.com")
        if cors_origins_str:
            self.CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
        else:
            self.CORS_ORIGINS = []

# Initialize settings
settings = Settings()