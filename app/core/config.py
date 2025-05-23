# app/core/config.py - Fixed configuration with async database URL

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/chatsassistant"
    )
    
    # Async version of database URL (replace postgresql:// with postgresql+asyncpg://)
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Convert sync database URL to async"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgres://"):
            return self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        else:
            return self.DATABASE_URL
    
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "ChatsAssistant API"
    VERSION: str = "0.1.0"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Security settings
    BCRYPT_ROUNDS: int = 12
    
    # Email settings (for future use)
    MAIL_USERNAME: Optional[str] = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: Optional[str] = os.getenv("MAIL_PASSWORD")
    MAIL_FROM: Optional[str] = os.getenv("MAIL_FROM")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER: Optional[str] = os.getenv("MAIL_SERVER")
    MAIL_TLS: bool = os.getenv("MAIL_TLS", "true").lower() == "true"
    MAIL_SSL: bool = os.getenv("MAIL_SSL", "false").lower() == "true"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
    ALLOWED_FILE_TYPES: list = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    # Redis settings (for caching and rate limiting)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Validate critical settings
if not settings.OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not set. AI features will not work.")

if settings.SECRET_KEY == "your-secret-key-change-this-in-production":
    print("⚠️  WARNING: Using default SECRET_KEY. Change this in production!")

# Log current database configuration
print(f"🗄️  Database URL: {settings.DATABASE_URL}")
print(f"🔄  Async Database URL: {settings.ASYNC_DATABASE_URL}")
print(f"🤖  OpenAI Model: {settings.OPENAI_MODEL}")
print(f"🌍  Environment: {settings.ENVIRONMENT}")
print(f"🐛  Debug Mode: {settings.DEBUG}")