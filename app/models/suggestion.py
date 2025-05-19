# File: app/models/suggestion.py (updated)
# Path: fanfix-api/app/models/suggestion.py

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import uuid

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class SuggestionRequest(BaseModel):
    message: str
    chat_history: List[ChatMessage] = []
    regenerate: bool = False
    creator_id: Optional[uuid.UUID] = None  # Optional override for selected creator

class SuggestionMessage(BaseModel):
    type: str  # "single" or "multi"
    messages: List[str]

class SuggestionResponse(BaseModel):
    suggestions: List[SuggestionMessage]