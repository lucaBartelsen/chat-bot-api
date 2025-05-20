# File: app/core/config.py (JSON approach with os.env)
# Path: fanfix-api/app/core/config.py

import os
import json
from typing import List, Any, Dict, Optional
from pydantic_settings import BaseSettings

def parse_json_env(env_name: str, default: Any = None) -> Any:
    """
    Parse a JSON-formatted environment variable.
    If the variable is not valid JSON or doesn't exist, return the default value.
    """
    env_value = os.environ.get(env_name)
    if not env_value:
        return default
    
    try:
        return json.loads(env_value)
    except json.JSONDecodeError:
        print(f"Warning: Environment variable {env_name} is not valid JSON. Using default value.")
        return default

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChatAssist API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "your-secret-key")
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "your-jwt-secret")
    JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_MINUTES: int = int(os.environ.get("JWT_EXPIRES_MINUTES", "1440"))
    
    # Database
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/chat_assistant_db"
    )
    
    # Default CORS origins if not set in environment
    CORS_ORIGINS: List[str] = [
        "https://chatsassistant.com", 
        "https://*.chatsassistant.com", 
        "http://localhost:3000"
    ]
    
    # Domain
    DOMAIN: str = os.environ.get("DOMAIN", "chatsassistant.com")
    
    # OpenAI
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = os.environ.get("DEFAULT_MODEL", "gpt-3.5-turbo")
    
    # Rate limiting
    RATE_LIMIT_MAX: int = int(os.environ.get("RATE_LIMIT_MAX", "100"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.environ.get("RATE_LIMIT_WINDOW_MINUTES", "15"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Ignore extra fields like POSTGRES_PASSWORD
        extra = "ignore"

# Initialize settings
settings = Settings()

# Override CORS_ORIGINS from environment if present
# This ensures that if the environment variable exists but is not valid JSON,
# we still have the default values
cors_origins_from_env = parse_json_env("CORS_ORIGINS")
if cors_origins_from_env:
    settings.CORS_ORIGINS = cors_origins_from_env