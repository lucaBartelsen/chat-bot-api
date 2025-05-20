# File: app/auth/models.py (updated)
# Path: fanfix-api/app/auth/models.py

from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr, Field
from fastapi_users import schemas
from datetime import datetime

# User base model
class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr = Field(..., description="User's email address")
    is_active: bool = Field(True, description="Whether the user is active")
    is_superuser: bool = Field(False, description="Whether the user is a superuser")
    is_verified: bool = Field(False, description="Whether the user is verified")
    created_at: Optional[datetime] = Field(None, description="When the user was created")

    class Config:
        from_attributes = True

# User with ID (main model)
class User(UserBase):
    """User model with UUID IDs"""
    id: uuid.UUID = Field(..., description="User's UUID")

# User creation model
class UserCreate(schemas.BaseUserCreate):
    """User creation model"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    is_active: Optional[bool] = Field(True, description="Whether the user is active")
    is_superuser: Optional[bool] = Field(False, description="Whether the user is a superuser")
    is_verified: Optional[bool] = Field(False, description="Whether the user is verified")

# User update model
class UserUpdate(schemas.BaseUserUpdate):
    """User update model"""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: Optional[str] = Field(None, description="User's password")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")
    is_superuser: Optional[bool] = Field(None, description="Whether the user is a superuser")
    is_verified: Optional[bool] = Field(None, description="Whether the user is verified")

# Database model with hashed password
class UserDB(UserBase):
    """User database model"""
    id: uuid.UUID = Field(..., description="User's UUID")
    hashed_password: str = Field(..., description="User's hashed password")

    class Config:
        from_attributes = True

# User Preferences Models
class UserPreferencesBase(BaseModel):
    """Base model for user preferences"""
    selected_creator_id: Optional[uuid.UUID] = Field(None, description="ID of the selected creator")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    model_name: Optional[str] = Field(None, description="Model name")
    num_suggestions: Optional[int] = Field(None, description="Number of suggestions")

class UserPreferencesCreate(UserPreferencesBase):
    """Model for creating user preferences"""
    pass

class UserPreferencesUpdate(UserPreferencesBase):
    """Model for updating user preferences"""
    pass

class UserPreferencesRead(UserPreferencesBase):
    """Model for reading user preferences"""
    user_id: uuid.UUID = Field(..., description="User ID")

    class Config:
        from_attributes = True