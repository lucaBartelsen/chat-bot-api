# app/api/suggestions.py - Fixed to use AsyncSession and store_conversation method

import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import openai

from app.models.suggestion import SuggestionRequest, SuggestionResponse
from app.models.creator import (
    Creator, 
    CreatorStyle, 
    StyleExample, 
    ResponseExample, 
    VectorStore
)
from app.models.user import User, UserPreference
from app.core.database import get_session
from app.auth.users import get_current_active_user
from app.services.ai_service import AIService
from app.services.vector_service import VectorService
from app.api.dependencies import get_ai_service, get_vector_service

router = APIRouter()

@router.post("/", response_model=SuggestionResponse)
async def get_suggestions(
    request: SuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Get AI suggestions for a message based on creator style and examples
    """
    # Get user preferences
    prefs_query = select(UserPreference).where(UserPreference.user_id == current_user.id)
    prefs_result = await session.execute(prefs_query)
    preferences = prefs_result.scalar_one_or_none()
    
    # Get creator
    creator_query = select(Creator).where(Creator.id == request.creator_id)
    creator_result = await session.execute(creator_query)
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {request.creator_id} not found"
        )
    
    # Get creator style
    style_query = select(CreatorStyle).where(CreatorStyle.creator_id == request.creator_id)
    style_result = await session.execute(style_query)
    style = style_result.scalar_one_or_none()
    
    # Set model and suggestion count from request or preferences
    model = request.model or (preferences.default_model if preferences else "gpt-4")
    suggestion_count = request.suggestion_count or (preferences.suggestion_count if preferences else 3)
    
    try:
        # Use comprehensive method to find examples and generate suggestions
        suggestions, model_used, processing_time = await ai_service.find_and_use_examples(
            request=request,
            creator=creator,
            style=style,
            vector_service=vector_service,
            similarity_threshold=request.similarity_threshold or 0.7,
            style_examples_limit=3,
            response_examples_limit=2
        )
        
        # If successful, store this conversation in vector store
        if len(suggestions) > 0:
            # Generate embedding for fan message
            embedding = await ai_service.generate_embedding(request.fan_message)
            
            # Store the best suggestion (highest confidence)
            best_suggestion = max(suggestions, key=lambda s: s.confidence)
            
            # FIXED: Store in vector database using store_conversation method
            await vector_service.store_conversation(
                creator_id=request.creator_id,
                fan_message=request.fan_message,
                creator_response=best_suggestion.text,
                embedding=embedding
            )
        
        # Create response
        response = SuggestionResponse(
            creator_id=request.creator_id,
            fan_message=request.fan_message,
            suggestions=suggestions,
            model_used=model_used,
            processing_time=processing_time,
            similar_conversation_count=0  # This is updated in vector_service
        )
        
        return response
    
    except openai.OpenAIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {str(e)}"
        )

@router.get("/stats")
async def get_suggestion_stats(
    current_user: User = Depends(get_current_active_user),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Get statistics about stored conversations and examples
    """
    stats = await vector_service.get_statistics()
    return stats

@router.post("/clear")
async def clear_stored_vectors(
    creator_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Clear stored vectors (conversations and examples), optionally for a specific creator
    """
    # Only admins can clear conversations
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to clear stored vectors"
        )
    
    deleted_counts = await vector_service.clear_vectors(creator_id)
    
    return {
        "deleted_counts": deleted_counts,
        "creator_id": creator_id,
        "timestamp": time.time()
    }

@router.post("/store-feedback")
async def store_feedback(
    creator_id: int = Body(...),
    fan_message: str = Body(...),
    selected_response: str = Body(...),
    current_user: User = Depends(get_current_active_user),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Store feedback about which response the user selected
    """
    try:
        # Generate embedding for fan message
        embedding = await ai_service.generate_embedding(fan_message)
        
        # FIXED: Store in vector database using store_conversation method
        vector = await vector_service.store_conversation(
            creator_id=creator_id,
            fan_message=fan_message,
            creator_response=selected_response,
            embedding=embedding
        )
        
        return {
            "status": "success",
            "message": "Feedback stored successfully",
            "vector_id": vector.id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing feedback: {str(e)}"
        )