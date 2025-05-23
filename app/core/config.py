# app/core/config.py - Complete fixed configuration

import os
import json
from typing import Optional, List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field


class Settings(BaseSettings):
    """Application settings with all environment variables properly defined"""
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@db:5432/chatsassistant-db"
    SYNC_DATABASE_URL: Optional[str] = None
    
    # Individual PostgreSQL components (for Docker environment)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "chatsassistant-db"
    
    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Convert sync database URL to async"""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        else:
            return url
    
    DATABASE_ECHO: bool = False
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "ChatsAssistant API"
    VERSION: str = "0.1.0"
    
    # CORS settings
    CORS_ORIGINS: str = '["http://localhost:3000", "https://chatsassistant.com"]'
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or return as-is if already a list"""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # If not JSON, split by comma
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else [v]
    
    @computed_field
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """Get CORS origins as a list"""
        origins = self.CORS_ORIGINS
        if isinstance(origins, str):
            try:
                parsed = json.loads(origins)
                return parsed if isinstance(parsed, list) else [origins]
            except json.JSONDecodeError:
                return [origin.strip() for origin in origins.split(",") if origin.strip()]
        return origins if isinstance(origins, list) else [origins]
    
    # Docker/deployment settings
    DOMAIN_NAME: str = "chatsassistant.com"
    
    # Security settings
    BCRYPT_ROUNDS: int = 12
    
    # Email settings (for future use)
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_PORT: int = 587
    MAIL_SERVER: Optional[str] = None
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File upload settings
    MAX_FILE_SIZE: int = 10485760  # 10MB default
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    # Redis settings (for caching and rate limiting)
    REDIS_URL: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Pydantic configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
        populate_by_name=True,
    )


# Create settings instance
settings = Settings()

# Validation and logging
def validate_and_log_settings():
    """Validate critical settings and log configuration"""
    print(f"🏗️  Initializing {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"🌍  Environment: {settings.ENVIRONMENT}")
    print(f"🐛  Debug Mode: {settings.DEBUG}")
    
    # Database
    print(f"🗄️  Database URL: {settings.DATABASE_URL}")
    print(f"🔄  Async Database URL: {settings.ASYNC_DATABASE_URL}")
    print(f"👤  Database User: {settings.POSTGRES_USER}")
    print(f"🏠  Database Name: {settings.POSTGRES_DB}")
    
    # Security
    if settings.SECRET_KEY == "your-secret-key-change-this-in-production":
        print("⚠️  WARNING: Using default SECRET_KEY. Change this in production!")
    else:
        print(f"🔐  Secret Key: {settings.SECRET_KEY[:10]}...")
    
    # OpenAI
    if not settings.OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not set. AI features will not work.")
    else:
        print(f"🤖  OpenAI API Key: Set (ends with ...{settings.OPENAI_API_KEY[-4:] if len(settings.OPENAI_API_KEY) > 8 else 'Set'})")
    
    print(f"🤖  OpenAI Model: {settings.OPENAI_MODEL}")
    
    # CORS
    try:
        cors_origins = settings.BACKEND_CORS_ORIGINS
        print(f"🌐  CORS Origins: {cors_origins}")
    except Exception as e:
        print(f"⚠️  CORS Origins parsing error: {e}")
    
    # Domain
    print(f"🌐  Domain: {settings.DOMAIN_NAME}")
    
    print("✅  Settings validation complete")


# Run validation when module is imported
validate_and_log_settings()