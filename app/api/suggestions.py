import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
import openai

from app.models.suggestion import SuggestionRequest, SuggestionResponse
from app.models.creator import Creator, CreatorStyle, StyleExample, VectorStore
from app.models.user import User, UserPreference
from app.core.database import get_session
from app.auth.users import get_current_active_user
from app.services.ai_service import AIService
from app.services.vector_service import VectorService

router = APIRouter()

@router.post("/", response_model=SuggestionResponse)
async def get_suggestions(
    request: SuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Get AI suggestions for a message based on creator style
    """
    # Get user preferences
    prefs_query = select(UserPreference).where(UserPreference.user_id == current_user.id)
    prefs_result = await session.execute(prefs_query)
    preferences = prefs_result.scalar_one_or_none()
    
    # Get OpenAI API key from preferences or settings
    api_key = preferences.openai_api_key if preferences and preferences.openai_api_key else None
    
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
    
    # Get style examples
    examples_query = select(StyleExample).where(StyleExample.creator_id == request.creator_id).limit(5)
    examples_result = await session.execute(examples_query)
    examples = examples_result.scalars().all()
    
    # Initialize services
    ai_service = AIService(api_key=api_key)
    vector_service = VectorService(session=session)
    
    # Set model and suggestion count from request or preferences
    model = request.model or (preferences.default_model if preferences else "gpt-4")
    suggestion_count = request.suggestion_count or (preferences.suggestion_count if preferences else 3)
    
    similar_conversations = []
    
    try:
        # Generate embedding for fan message (if using vector search)
        if request.use_similar_conversations:
            # Create embedding using OpenAI
            response = await ai_service.client.embeddings.create(
                model="text-embedding-ada-002",
                input=request.fan_message
            )
            embedding = response.data[0].embedding
            
            # Find similar conversations
            similar_conversations = await vector_service.find_similar_conversations(
                creator_id=request.creator_id,
                embedding=embedding,
                similarity_threshold=request.similarity_threshold or 0.7,
                limit=5
            )
        
        # Generate suggestions
        suggestions, model_used, processing_time = await ai_service.generate_suggestions(
            request=request,
            creator=creator,
            style=style,
            examples=examples,
            similar_conversations=similar_conversations
        )
        
        # Create response
        response = SuggestionResponse(
            creator_id=request.creator_id,
            fan_message=request.fan_message,
            suggestions=suggestions,
            model_used=model_used,
            processing_time=processing_time,
            similar_conversation_count=len(similar_conversations)
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
    session: Session = Depends(get_session)
):
    """
    Get statistics about stored conversations
    """
    vector_service = VectorService(session=session)
    stats = await vector_service.get_statistics()
    return stats

@router.post("/clear")
async def clear_stored_conversations(
    creator_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """
    Clear stored conversations, optionally for a specific creator
    """
    # Only admins can clear conversations
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to clear stored conversations"
        )
    
    vector_service = VectorService(session=session)
    deleted_count = await vector_service.clear_vectors(creator_id)
    
    return {
        "deleted_count": deleted_count,
        "creator_id": creator_id,
        "timestamp": time.time()
    }