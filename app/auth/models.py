# File: app/auth/models.py (updated)
# Path: fanfix-api/app/auth/models.py

from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr
from fastapi_users.schemas import BaseUserCreate, BaseUserUpdate
from datetime import datetime

# User base model
class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# User with ID (main model)
class User(UserBase):
    """User model with UUID IDs"""
    id: uuid.UUID

# User creation model
class UserCreate(BaseUserCreate):
    """User creation model"""
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False

# User update model
class UserUpdate(BaseUserUpdate):
    """User update model"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None

# Database model with hashed password
class UserDB(UserBase):
    """User database model"""
    id: uuid.UUID
    hashed_password: str

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