from datetime import datetime
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field

# Request model for getting AI suggestions
class SuggestionRequest(BaseModel):
    creator_id: int
    fan_message: str
    model: Optional[str] = None
    suggestion_count: Optional[int] = 3
    use_similar_conversations: bool = True
    similarity_threshold: Optional[float] = 0.7
    
# Single message suggestion
class MessageSuggestion(BaseModel):
    text: str
    confidence: float = 1.0
    
# Response with multiple suggestion options
class SuggestionResponse(BaseModel):
    creator_id: int
    fan_message: str
    suggestions: List[MessageSuggestion]
    model_used: str
    processing_time: float
    similar_conversation_count: int = 0