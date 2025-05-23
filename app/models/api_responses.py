# app/models/api_responses.py - Clean API response models without embeddings

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Clean response models for API serialization (no embeddings)

class StyleExampleResponse(BaseModel):
    """Response model for style examples - excludes embedding field"""
    id: int
    creator_id: int
    fan_message: str
    creator_response: str
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CreatorResponseResponse(BaseModel):
    """Response model for individual creator responses"""
    id: int
    example_id: int
    response_text: str
    ranking: Optional[int] = None

class ResponseExampleResponse(BaseModel):
    """Response model for response examples - excludes embedding field"""
    id: int
    creator_id: int
    fan_message: str
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    responses: List[CreatorResponseResponse] = []

class VectorStoreResponse(BaseModel):
    """Response model for vector store - excludes embedding field"""
    id: int
    creator_id: int
    fan_message: str
    creator_response: str
    similarity_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

# Pagination response models
class StyleExamplesResponse(BaseModel):
    items: List[StyleExampleResponse]
    total: int
    page: int
    size: int
    pages: int

class ResponseExamplesResponse(BaseModel):
    items: List[ResponseExampleResponse]
    total: int
    page: int
    size: int
    pages: int