from datetime import datetime
from typing import Any, List, Optional, Dict
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON
from pydantic import EmailStr

from app.models.core import BaseModel

# User model
class User(BaseModel, table=True):
    __tablename__ = "users"
    
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    is_admin: bool = False
    
    # Relationships
    preferences: Optional["UserPreference"] = Relationship(back_populates="user")

# User preferences
class UserPreference(BaseModel, table=True):
    __tablename__ = "user_preferences"
    
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", unique=True)
    openai_api_key: Optional[str] = None
    default_model: Optional[str] = "gpt-4"
    suggestion_count: int = 3
    selected_creators: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="preferences")