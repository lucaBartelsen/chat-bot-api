# File: app/auth/models.py
# Path: fanfix-api/app/auth/models.py

from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr
from fastapi_users import models
from datetime import datetime

# FastAPI Users models
class User(models.BaseUser):
    """User model with UUID IDs"""
    id: uuid.UUID
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime = None
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class UserCreate(models.BaseUserCreate):
    """User creation model"""
    email: EmailStr
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False

class UserUpdate(models.BaseUserUpdate):
    """User update model"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserDB(models.BaseUserDB):
    """User database model"""
    id: uuid.UUID
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime = None
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# User Preferences Models
class UserPreferencesBase(BaseModel):
    """Base model for user preferences"""
    selected_creator_id: Optional[uuid.UUID] = None
    openai_api_key: Optional[str] = None
    model_name: Optional[str] = None
    num_suggestions: Optional[int] = None

class UserPreferencesCreate(UserPreferencesBase):
    """Model for creating user preferences"""
    pass

class UserPreferencesUpdate(UserPreferencesBase):
    """Model for updating user preferences"""
    pass

class UserPreferencesRead(UserPreferencesBase):
    """Model for reading user preferences"""
    user_id: uuid.UUID

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True