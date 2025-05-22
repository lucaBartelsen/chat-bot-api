from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, text, func
from pgvector.sqlalchemy import Vector

# Base model for all SQLModel models
class BaseModel(SQLModel):
    """Base model with common fields"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),  # timezone-naive UTC
        sa_column=Column(
            "created_at", 
            nullable=False, 
            server_default=func.now()  # PostgreSQL's now() function
        )
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),  # timezone-naive UTC
        sa_column=Column(
            "updated_at", 
            nullable=False, 
            server_default=func.now(),  # PostgreSQL's now() function
            onupdate=func.now()  # Auto-update on modification
        )
    )
    
    class Config:
        arbitrary_types_allowed = True