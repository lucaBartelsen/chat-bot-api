# app/models/creator.py - Fixed to exclude embeddings from API responses

from datetime import datetime
from typing import Any, List, Optional, Dict
from sqlmodel import Field, Relationship, SQLModel
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, text, JSON, String, Integer
from pydantic import field_validator

from app.models.core import BaseModel

# Creator model (unchanged)
class Creator(BaseModel, table=True):
    __tablename__ = "creators"
    
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    
    # Relationships
    styles: List["CreatorStyle"] = Relationship(back_populates="creator")
    style_examples: List["StyleExample"] = Relationship(back_populates="creator")
    response_examples: List["ResponseExample"] = Relationship(back_populates="creator")

# Creator style configuration (unchanged)
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

# Style examples for reference (with embedding added but excluded from serialization)
class StyleExample(BaseModel, table=True):
    __tablename__ = "style_examples"
    
    creator_id: Optional[int] = Field(default=None, foreign_key="creators.id")
    fan_message: str
    creator_response: str
    category: Optional[str] = None
    
    # Vector embedding (1536 dimensions for OpenAI embedding)
    # FIXED: Exclude from serialization to prevent numpy array serialization error
    embedding: Optional[Any] = Field(
        default=None, 
        sa_column=Column(Vector(1536)),
        exclude=True  # This excludes it from Pydantic serialization
    )
    
    # Relationships
    creator: Optional[Creator] = Relationship(back_populates="style_examples")
    
    class Config:
        # Alternative way to exclude embedding from serialization
        fields = {"embedding": {"exclude": True}}

# New model for response examples with multiple responses
class ResponseExample(BaseModel, table=True):
    __tablename__ = "response_examples"
    
    creator_id: Optional[int] = Field(default=None, foreign_key="creators.id")
    fan_message: str
    category: Optional[str] = None
    
    # Vector embedding (1536 dimensions for OpenAI embedding)
    # FIXED: Exclude from serialization to prevent numpy array serialization error
    embedding: Optional[Any] = Field(
        default=None, 
        sa_column=Column(Vector(1536)),
        exclude=True  # This excludes it from Pydantic serialization
    )
    
    # Relationships
    creator: Optional[Creator] = Relationship(back_populates="response_examples")
    responses: List["CreatorResponse"] = Relationship(back_populates="example")
    
    class Config:
        # Alternative way to exclude embedding from serialization
        fields = {"embedding": {"exclude": True}}

# Model for individual creator responses to a response example
class CreatorResponse(BaseModel, table=True):
    __tablename__ = "creator_responses"
    
    example_id: Optional[int] = Field(default=None, foreign_key="response_examples.id")
    response_text: str
    ranking: Optional[int] = Field(default=0)  # Ranking for quality/preference (1-4)
    
    # Relationships
    example: Optional[ResponseExample] = Relationship(back_populates="responses")

# Vector store for conversation examples (embedding excluded from serialization)
class VectorStore(BaseModel, table=True):
    __tablename__ = "vector_store"
    
    creator_id: Optional[int] = Field(default=None, foreign_key="creators.id")
    fan_message: str
    creator_response: str
    
    # Vector embedding (1536 dimensions for OpenAI embedding)
    # FIXED: Exclude from serialization to prevent numpy array serialization error
    embedding: Any = Field(
        sa_column=Column(Vector(1536)),
        exclude=True  # This excludes it from Pydantic serialization
    )
    similarity_score: Optional[float] = None
    
    class Config:
        # Alternative way to exclude embedding from serialization
        fields = {"embedding": {"exclude": True}}