from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, text
from pgvector.sqlalchemy import Vector
from pydantic import validator

# Base model for all SQLModel models
class BaseModel(SQLModel):
    """Base model with common fields"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        arbitrary_types_allowed = True