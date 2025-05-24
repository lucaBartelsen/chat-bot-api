# app/models/user.py - Updated with better cascade relationships

from datetime import datetime
from typing import Any, List, Optional, Dict
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON, ForeignKey
from pydantic import EmailStr

from app.models.core import BaseModel

# User model with enhanced relationships
class User(BaseModel, table=True):
    __tablename__ = "users"
    
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    is_admin: bool = False
    
    # Enhanced relationships with cascade delete
    preferences: Optional["UserPreference"] = Relationship(
        back_populates="user",
        cascade_delete=True  # Delete preferences when user is deleted
    )

# User preferences with better structure
class UserPreference(BaseModel, table=True):
    __tablename__ = "user_preferences"
    
    user_id: Optional[int] = Field(
        default=None, 
        foreign_key="users.id", 
        unique=True,
        index=True
    )
    openai_api_key: Optional[str] = None
    default_model: str = "gpt-4"
    suggestion_count: int = 3
    selected_creators: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))
    
    # Enhanced settings
    max_suggestions_per_day: Optional[int] = Field(default=100)
    preferred_response_length: Optional[str] = Field(default="medium")  # short, medium, long
    enable_notifications: bool = Field(default=True)
    theme_preference: Optional[str] = Field(default="light")  # light, dark, auto
    language_preference: Optional[str] = Field(default="en")
    timezone: Optional[str] = Field(default="UTC")
    
    # API usage tracking
    api_calls_today: int = Field(default=0)
    last_api_call: Optional[datetime] = Field(default=None)
    total_api_calls: int = Field(default=0)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="preferences")

# Additional models for user activity tracking
class UserSession(BaseModel, table=True):
    __tablename__ = "user_sessions"
    
    user_id: int = Field(foreign_key="users.id", index=True)
    session_token: str = Field(index=True, unique=True)
    ip_address: Optional[str] = None