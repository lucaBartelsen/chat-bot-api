from datetime import datetime
from typing import Any, List, Optional, Dict
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, text
from pgvector.sqlalchemy import Vector
from pydantic import validator

# Base model for all SQLModel models
class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})