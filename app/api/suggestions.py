# File: app/api/suggestions.py (updated)
# Path: fanfix-api/app/api/suggestions.py

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
import uuid

from prisma import Prisma
from app.auth.models import User
from app.auth.users import current_active_user, get_prisma
from app.api.dependencies import require_api_key
from app.models.suggestion import (
    SuggestionRequest,
    SuggestionResponse,
    SuggestionMessage,
    ChatMessage
)
from app.services.ai_service import AIService
from app.services.vector_service import VectorService

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

@router.post("/", response_model=SuggestionResponse)
async def get_suggestions(
    request: SuggestionRequest,
    user_prefs = Depends(require_api_key),  # This dependency checks for API key
    current_user: User = Depends(current_active_user),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Get message suggestions for a fan message
    """
    # Initialize services
    ai_service = AIService(
        api_key=user_prefs.openaiApiKey,
        model_name=user_prefs.modelName or "gpt-3.5-turbo"
    )
    vector_service = VectorService()
    
    # Get creator style if available
    creator_style = None
    creator_id = user_prefs.selectedCreatorId
    if creator_id:
        creator = await prisma.creator.find_unique(
            where={"id": creator_id},
            include={"style": True}
        )
        if creator and creator.style:
            creator_style = creator.style
    
    # Get embedding for the fan message
    embedding = await ai_service.get_embedding(request.message)
    
    # Find similar conversations
    similar_conversations = []
    if creator_id:
        similar_conversations = await vector_service.find_similar_conversations(
            embedding=embedding,
            creator_id=creator_id,
            limit=3
        )
    
    # Get suggestions
    formatted_chat_history = [
        {"role": msg.role, "content": msg.content} 
        for msg in request.chat_history
    ]
    
    suggestions = await ai_service.get_suggestions(
        fan_message=request.message,
        chat_history=formatted_chat_history,
        creator_style=creator_style,
        similar_conversations=similar_conversations,
        num_suggestions=user_prefs.numSuggestions,
        regenerate=request.regenerate
    )
    
    # Store the conversation for future reference (but only if not regenerating)
    if creator_id and suggestions and not request.regenerate:
        first_suggestion = suggestions[0]
        creator_responses = first_suggestion["messages"]
        await vector_service.store_conversation(
            creator_id=creator_id,
            fan_message=request.message,
            creator_responses=creator_responses,
            embedding=embedding
        )
    
    # Format response
    return {"suggestions": suggestions}

@router.get("/stats", response_model=Dict[str, Any])
async def get_suggestion_stats(
    creator_id: uuid.UUID = None,
    current_user: User = Depends(current_active_user)
) -> Any:
    """
    Get statistics about stored conversations
    """
    vector_service = VectorService()
    stats = await vector_service.get_conversation_stats(
        creator_id=str(creator_id) if creator_id else None
    )
    return stats

@router.post("/clear", response_model=Dict[str, Any])
async def clear_stored_conversations(
    creator_id: uuid.UUID = None,
    current_user: User = Depends(current_active_user)
) -> Any:
    """
    Clear stored conversations
    """
    vector_service = VectorService()
    count = await vector_service.clear_conversations(
        creator_id=str(creator_id) if creator_id else None
    )
    return {
        "success": True,
        "cleared_count": count,
        "message": f"Successfully cleared {count} conversations"
    }