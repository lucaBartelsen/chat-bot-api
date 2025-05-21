from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from sqlmodel import DateTime, Field, Relationship, SQLModel
from sqlalchemy import Column, text
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from pydantic import validator

# Base model for all SQLModel models
class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc), sa_column=Column(DateTime, default=func.now(), nullable=False))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc),sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False))