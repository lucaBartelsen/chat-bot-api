from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
from openai import OpenAI

from app.core.database import get_session
from app.models.user import User, UserPreference
from app.auth.users import get_current_active_user
from app.services.ai_service import AIService
from app.services.vector_service import VectorService

async def get_openai_api_key(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
) -> Optional[str]:
    """
    Get OpenAI API key from user preferences
    """
    query = select(UserPreference).where(UserPreference.user_id == current_user.id)
    result = await session.execute(query)
    preferences = result.scalar_one_or_none()
    
    return preferences.openai_api_key if preferences else None

async def get_ai_service(
    api_key: Optional[str] = Depends(get_openai_api_key)
) -> AIService:
    """
    Get AI service with user's API key
    """
    return AIService(api_key=api_key)

async def get_vector_service(
    session: Session = Depends(get_session)
) -> VectorService:
    """
    Get vector service with database session
    """
    return VectorService(session=session)