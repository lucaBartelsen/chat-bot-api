from datetime import datetime
from typing import Any, List, Optional, Dict
from sqlmodel import Field, Relationship, SQLModel
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, text, JSON, String
from pydantic import validator

from app.models.core import BaseModel

# Creator model
class Creator(BaseModel, table=True):
    __tablename__ = "creators"
    
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    
    # Relationships
    styles: List["CreatorStyle"] = Relationship(back_populates="creator")
    examples: List["StyleExample"] = Relationship(back_populates="creator")

# Creator style configuration
class CreatorStyle(BaseModel, table=True):
    __tablename__ = "creator_styles"
    
    creator_id: Optional[int] = Field(default=None, foreign_key="creators.id")
    
    # Style configuration
    approved_emojis: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    case_style: Optional[str] = None  # lowercase, sentence, custom
    text_replacements: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    sentence_separators: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    punctuation_rules: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    common_abbreviations: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    message_length_preferences: Optional[Dict[str, int]] = Field(default=None, sa_column=Column(JSON))
    style_instructions: Optional[str] = None
    tone_range: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Relationships
    creator: Optional[Creator] = Relationship(back_populates="styles")

# Style examples for reference
class StyleExample(BaseModel, table=True):
    __tablename__ = "style_examples"
    
    creator_id: Optional[int] = Field(default=None, foreign_key="creators.id")
    fan_message: str
    creator_response: str
    category: Optional[str] = None
    
    # Relationships
    creator: Optional[Creator] = Relationship(back_populates="examples")

# Vector store for conversation examples
class VectorStore(BaseModel, table=True):
    __tablename__ = "vector_store"
    
    creator_id: Optional[int] = Field(default=None, foreign_key="creators.id")
    fan_message: str
    creator_response: str
    
    # Vector embedding (1536 dimensions for OpenAI embedding)
    embedding: Any = Field(sa_column=Column(Vector(1536)))
    similarity_score: Optional[float] = None