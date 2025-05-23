# app/api/dependencies.py - Fixed dependency injection for async services

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.ai_service import AIService
from app.services.vector_service import VectorService
from app.core.config import settings


async def get_ai_service() -> AIService:
    """Get AIService instance"""
    return AIService(api_key=settings.OPENAI_API_KEY)


async def get_vector_service(session: AsyncSession = Depends(get_session)) -> VectorService:
    """Get VectorService instance with async session"""
    return VectorService(session=session)


# Additional dependency for services that need both AI and Vector services
async def get_services(
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
) -> tuple[AIService, VectorService, AsyncSession]:
    """Get all required services for complex operations"""
    return ai_service, vector_service, session