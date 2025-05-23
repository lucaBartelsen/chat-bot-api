# app/api/examples.py - Fixed to use clean response models

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from pydantic import BaseModel

from app.core.database import get_session
from app.models.creator import (
    Creator, 
    StyleExample, 
    ResponseExample,
    CreatorResponse
)
from app.auth.users import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.services.vector_service import VectorService
from app.services.ai_service import AIService
from app.api.dependencies import get_ai_service, get_vector_service

# Clean response models (no embeddings to avoid numpy serialization issues)
class StyleExampleResponse(BaseModel):
    """Response model for style examples - excludes embedding field"""
    id: int
    creator_id: int
    fan_message: str
    creator_response: str
    category: Optional[str] = None
    created_at: str  # Use string for datetime
    updated_at: str

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
    created_at: str  # Use string for datetime
    updated_at: str
    responses: List[CreatorResponseResponse] = []

# Request models
class StyleExampleCreate(BaseModel):
    fan_message: str
    creator_response: str
    category: Optional[str] = None

class CreatorResponseItem(BaseModel):
    response_text: str
    ranking: Optional[int] = None

class ResponseExampleCreate(BaseModel):
    fan_message: str
    responses: List[CreatorResponseItem]
    category: Optional[str] = None

# Create router
router = APIRouter()

# Style Examples Endpoints
@router.post("/{creator_id}/style-examples", response_model=StyleExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_style_example(
    creator_id: int,
    example: StyleExampleCreate,
    admin_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Create a new style example with vector embedding"""
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    # Generate embedding using OpenAI
    try:
        # Generate embedding for fan message (more relevant for searching)
        embedding_response = await ai_service.client.embeddings.create(
            model="text-embedding-ada-002",
            input=example.fan_message
        )
        embedding = embedding_response.data[0].embedding
        
        # Store style example with embedding
        stored_example = await vector_service.store_style_example(
            creator_id=creator_id,
            fan_message=example.fan_message,
            creator_response=example.creator_response,
            category=example.category,
            embedding=embedding
        )
        
        # Return clean response model
        return StyleExampleResponse(
            id=stored_example.id,
            creator_id=stored_example.creator_id,
            fan_message=stored_example.fan_message,
            creator_response=stored_example.creator_response,
            category=stored_example.category,
            created_at=stored_example.created_at.isoformat(),
            updated_at=stored_example.updated_at.isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating embedding: {str(e)}"
        )

@router.get("/{creator_id}/style-examples", response_model=List[StyleExampleResponse])
async def get_style_examples(
    creator_id: int,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get style examples for a creator"""
    
    # Base query
    query = select(StyleExample).where(StyleExample.creator_id == creator_id)
    
    # Add category filter if provided
    if category:
        query = query.where(StyleExample.category == category)
    
    # Add pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    examples = result.scalars().all()
    
    # Convert to clean response models
    clean_examples = []
    for example in examples:
        clean_examples.append(StyleExampleResponse(
            id=example.id,
            creator_id=example.creator_id,
            fan_message=example.fan_message,
            creator_response=example.creator_response,
            category=example.category,
            created_at=example.created_at.isoformat(),
            updated_at=example.updated_at.isoformat()
        ))
    
    return clean_examples

@router.delete("/{creator_id}/style-examples/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style_example(
    creator_id: int,
    example_id: int,
    admin_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a style example"""
    
    # Get example
    query = select(StyleExample).where(
        StyleExample.id == example_id,
        StyleExample.creator_id == creator_id
    )
    result = await session.execute(query)
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Style example with ID {example_id} not found for creator {creator_id}"
        )
    
    # Delete example
    await session.delete(example)
    await session.commit()
    
    return None

# Response Examples Endpoints
@router.post("/{creator_id}/response-examples", response_model=ResponseExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_response_example(
    creator_id: int,
    example: ResponseExampleCreate,
    admin_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Create a new response example with multiple responses and vector embedding"""
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    # Check if we have at least one response
    if not example.responses or len(example.responses) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one response is required"
        )
    
    try:
        # Generate embedding using OpenAI
        embedding_response = await ai_service.client.embeddings.create(
            model="text-embedding-ada-002",
            input=example.fan_message
        )
        embedding = embedding_response.data[0].embedding
        
        # Extract response texts and rankings
        response_texts = [resp.response_text for resp in example.responses]
        rankings = [resp.ranking for resp in example.responses if resp.ranking is not None]
        
        # Store response example with embedding
        stored_example = await vector_service.store_response_example(
            creator_id=creator_id,
            fan_message=example.fan_message,
            responses=response_texts,
            rankings=rankings if rankings else None,
            category=example.category,
            embedding=embedding
        )
        
        # Get complete example with responses for clean response
        query = (
            select(ResponseExample)
            .where(ResponseExample.id == stored_example.id)
        )
        result = await session.execute(query)
        complete_example = result.scalar_one_or_none()
        
        # Convert to clean response model
        clean_responses = []
        if complete_example and complete_example.responses:
            for resp in complete_example.responses:
                clean_responses.append(CreatorResponseResponse(
                    id=resp.id,
                    example_id=resp.example_id,
                    response_text=resp.response_text,
                    ranking=resp.ranking
                ))
        
        return ResponseExampleResponse(
            id=complete_example.id,
            creator_id=complete_example.creator_id,
            fan_message=complete_example.fan_message,
            category=complete_example.category,
            created_at=complete_example.created_at.isoformat(),
            updated_at=complete_example.updated_at.isoformat(),
            responses=clean_responses
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating response example: {str(e)}"
        )

# Update all remaining Session references to AsyncSession
@router.get("/{creator_id}/response-examples", response_model=List[ResponseExampleResponse])
async def get_response_examples(
    creator_id: int,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get response examples for a creator"""
    
    # Base query
    query = select(ResponseExample).where(ResponseExample.creator_id == creator_id)
    
    # Add category filter if provided
    if category:
        query = query.where(ResponseExample.category == category)
    
    # Add pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    examples = result.scalars().all()
    
    # Convert to clean response models
    clean_examples = []
    for example in examples:
        clean_responses = []
        if example.responses:
            for resp in example.responses:
                clean_responses.append(CreatorResponseResponse(
                    id=resp.id,
                    example_id=resp.example_id,
                    response_text=resp.response_text,
                    ranking=resp.ranking
                ))
        
        clean_examples.append(ResponseExampleResponse(
            id=example.id,
            creator_id=example.creator_id,
            fan_message=example.fan_message,
            category=example.category,
            created_at=example.created_at.isoformat(),
            updated_at=example.updated_at.isoformat(),
            responses=clean_responses
        ))
    
    return clean_examples

@router.get("/{creator_id}/response-examples/{example_id}", response_model=ResponseExampleResponse)
async def get_response_example(
    creator_id: int,
    example_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific response example with all responses"""
    
    # Get example
    query = select(ResponseExample).where(
        ResponseExample.id == example_id,
        ResponseExample.creator_id == creator_id
    )
    result = await session.execute(query)
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response example with ID {example_id} not found for creator {creator_id}"
        )
    
    # Convert to clean response model
    clean_responses = []
    if example.responses:
        for resp in example.responses:
            clean_responses.append(CreatorResponseResponse(
                id=resp.id,
                example_id=resp.example_id,
                response_text=resp.response_text,
                ranking=resp.ranking
            ))
    
    return ResponseExampleResponse(
        id=example.id,
        creator_id=example.creator_id,
        fan_message=example.fan_message,
        category=example.category,
        created_at=example.created_at.isoformat(),
        updated_at=example.updated_at.isoformat(),
        responses=clean_responses
    )

@router.delete("/{creator_id}/response-examples/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_response_example(
    creator_id: int,
    example_id: int,
    admin_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a response example and all associated responses"""
    
    # Get example
    query = select(ResponseExample).where(
        ResponseExample.id == example_id,
        ResponseExample.creator_id == creator_id
    )
    result = await session.execute(query)
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response example with ID {example_id} not found for creator {creator_id}"
        )
    
    # Delete example (responses will cascade delete)
    await session.delete(example)
    await session.commit()
    
    return None
    """Get response examples for a creator"""
    
    # Base query
    query = select(ResponseExample).where(ResponseExample.creator_id == creator_id)
    
    # Add category filter if provided
    if category:
        query = query.where(ResponseExample.category == category)
    
    # Add pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    examples = result.scalars().all()
    
    # Convert to clean response models
    clean_examples = []
    for example in examples:
        clean_responses = []
        if example.responses:
            for resp in example.responses:
                clean_responses.append(CreatorResponseResponse(
                    id=resp.id,
                    example_id=resp.example_id,
                    response_text=resp.response_text,
                    ranking=resp.ranking
                ))
        
        clean_examples.append(ResponseExampleResponse(
            id=example.id,
            creator_id=example.creator_id,
            fan_message=example.fan_message,
            category=example.category,
            created_at=example.created_at.isoformat(),
            updated_at=example.updated_at.isoformat(),
            responses=clean_responses
        ))
    
    return clean_examples

@router.get("/{creator_id}/response-examples/{example_id}", response_model=ResponseExampleResponse)
async def get_response_example(
    creator_id: int,
    example_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Get a specific response example with all responses"""
    
    # Get example
    query = select(ResponseExample).where(
        ResponseExample.id == example_id,
        ResponseExample.creator_id == creator_id
    )
    result = await session.execute(query)
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response example with ID {example_id} not found for creator {creator_id}"
        )
    
    # Convert to clean response model
    clean_responses = []
    if example.responses:
        for resp in example.responses:
            clean_responses.append(CreatorResponseResponse(
                id=resp.id,
                example_id=resp.example_id,
                response_text=resp.response_text,
                ranking=resp.ranking
            ))
    
    return ResponseExampleResponse(
        id=example.id,
        creator_id=example.creator_id,
        fan_message=example.fan_message,
        category=example.category,
        created_at=example.created_at.isoformat(),
        updated_at=example.updated_at.isoformat(),
        responses=clean_responses
    )

@router.delete("/{creator_id}/response-examples/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_response_example(
    creator_id: int,
    example_id: int,
    admin_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """Delete a response example and all associated responses"""
    
    # Get example
    query = select(ResponseExample).where(
        ResponseExample.id == example_id,
        ResponseExample.creator_id == creator_id
    )
    result = await session.execute(query)
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response example with ID {example_id} not found for creator {creator_id}"
        )
    
    # Delete example (responses will cascade delete)
    await session.delete(example)
    await session.commit()
    
    return None

# Similar Examples Search Endpoints - Fix remaining Session references
@router.post("/{creator_id}/similar-style-examples", response_model=List[StyleExampleResponse])
async def find_similar_style_examples(
    creator_id: int,
    fan_message: str = Body(...),
    category: Optional[str] = None,
    similarity_threshold: float = Body(0.7),
    limit: int = Body(5),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Find style examples similar to a given fan message"""
    
    try:
        # Generate embedding using OpenAI
        embedding_response = await ai_service.client.embeddings.create(
            model="text-embedding-ada-002",
            input=fan_message
        )
        embedding = embedding_response.data[0].embedding
        
        # Find similar examples
        similar_examples = await vector_service.find_similar_style_examples(
            creator_id=creator_id,
            embedding=embedding,
            similarity_threshold=similarity_threshold,
            limit=limit,
            category=category
        )
        
        # Convert to clean response models
        clean_examples = []
        for example, _ in similar_examples:
            clean_examples.append(StyleExampleResponse(
                id=example.id,
                creator_id=example.creator_id,
                fan_message=example.fan_message,
                creator_response=example.creator_response,
                category=example.category,
                created_at=example.created_at.isoformat(),
                updated_at=example.updated_at.isoformat()
            ))
        
        return clean_examples
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding similar examples: {str(e)}"
        )

@router.post("/{creator_id}/similar-response-examples", response_model=List[ResponseExampleResponse])
async def find_similar_response_examples(
    creator_id: int,
    fan_message: str = Body(...),
    category: Optional[str] = None,
    similarity_threshold: float = Body(0.7),
    limit: int = Body(5),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Find response examples similar to a given fan message"""
    
    try:
        # Generate embedding using OpenAI
        embedding_response = await ai_service.client.embeddings.create(
            model="text-embedding-ada-002",
            input=fan_message
        )
        embedding = embedding_response.data[0].embedding
        
        # Find similar examples
        similar_examples = await vector_service.find_similar_response_examples(
            creator_id=creator_id,
            embedding=embedding,
            similarity_threshold=similarity_threshold,
            limit=limit,
            category=category
        )
        
        # Convert to clean response models
        clean_examples = []
        for example, _ in similar_examples:
            clean_responses = []
            if example.responses:
                for resp in example.responses:
                    clean_responses.append(CreatorResponseResponse(
                        id=resp.id,
                        example_id=resp.example_id,
                        response_text=resp.response_text,
                        ranking=resp.ranking
                    ))
            
            clean_examples.append(ResponseExampleResponse(
                id=example.id,
                creator_id=example.creator_id,
                fan_message=example.fan_message,
                category=example.category,
                created_at=example.created_at.isoformat(),
                updated_at=example.updated_at.isoformat(),
                responses=clean_responses
            ))
        
        return clean_examples
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding similar examples: {str(e)}"
        )

# Bulk operations - Fix remaining Session references
@router.post("/{creator_id}/bulk-style-examples", status_code=status.HTTP_201_CREATED)
async def bulk_create_style_examples(
    creator_id: int,
    examples: List[StyleExampleCreate],
    admin_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Create multiple style examples in bulk"""
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    created_count = 0
    errors = []
    
    for idx, example in enumerate(examples):
        try:
            # Generate embedding
            embedding_response = await ai_service.client.embeddings.create(
                model="text-embedding-ada-002",
                input=example.fan_message
            )
            embedding = embedding_response.data[0].embedding
            
            # Store example
            await vector_service.store_style_example(
                creator_id=creator_id,
                fan_message=example.fan_message,
                creator_response=example.creator_response,
                category=example.category,
                embedding=embedding
            )
            
            created_count += 1
            
        except Exception as e:
            errors.append({
                "index": idx,
                "fan_message": example.fan_message[:50] + "...",
                "error": str(e)
            })
    
    return {
        "success": True,
        "created_count": created_count,
        "total_count": len(examples),
        "errors": errors if errors else None
    }

@router.post("/{creator_id}/bulk-response-examples", status_code=status.HTTP_201_CREATED)
async def bulk_create_response_examples(
    creator_id: int,
    examples: List[ResponseExampleCreate],
    admin_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Create multiple response examples in bulk"""
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    created_count = 0
    errors = []
    
    for idx, example in enumerate(examples):
        try:
            # Check if we have at least one response
            if not example.responses or len(example.responses) == 0:
                raise ValueError("At least one response is required")
            
            # Generate embedding
            embedding_response = await ai_service.client.embeddings.create(
                model="text-embedding-ada-002",
                input=example.fan_message
            )
            embedding = embedding_response.data[0].embedding
            
            # Extract response texts and rankings
            response_texts = [resp.response_text for resp in example.responses]
            rankings = [resp.ranking for resp in example.responses if resp.ranking is not None]
            
            # Store example
            await vector_service.store_response_example(
                creator_id=creator_id,
                fan_message=example.fan_message,
                responses=response_texts,
                rankings=rankings if rankings else None,
                category=example.category,
                embedding=embedding
            )
            
            created_count += 1
            
        except Exception as e:
            errors.append({
                "index": idx,
                "fan_message": example.fan_message[:50] + "...",
                "error": str(e)
            })
    
    return {
        "success": True,
        "created_count": created_count,
        "total_count": len(examples),
        "errors": errors if errors else None
    }
@router.post("/{creator_id}/similar-style-examples", response_model=List[StyleExampleResponse])
async def find_similar_style_examples(
    creator_id: int,
    fan_message: str = Body(...),
    category: Optional[str] = None,
    similarity_threshold: float = Body(0.7),
    limit: int = Body(5),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Find style examples similar to a given fan message"""
    
    try:
        # Generate embedding using OpenAI
        embedding_response = await ai_service.client.embeddings.create(
            model="text-embedding-ada-002",
            input=fan_message
        )
        embedding = embedding_response.data[0].embedding
        
        # Find similar examples
        similar_examples = await vector_service.find_similar_style_examples(
            creator_id=creator_id,
            embedding=embedding,
            similarity_threshold=similarity_threshold,
            limit=limit,
            category=category
        )
        
        # Convert to clean response models
        clean_examples = []
        for example, _ in similar_examples:
            clean_examples.append(StyleExampleResponse(
                id=example.id,
                creator_id=example.creator_id,
                fan_message=example.fan_message,
                creator_response=example.creator_response,
                category=example.category,
                created_at=example.created_at.isoformat(),
                updated_at=example.updated_at.isoformat()
            ))
        
        return clean_examples
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding similar examples: {str(e)}"
        )

@router.post("/{creator_id}/similar-response-examples", response_model=List[ResponseExampleResponse])
async def find_similar_response_examples(
    creator_id: int,
    fan_message: str = Body(...),
    category: Optional[str] = None,
    similarity_threshold: float = Body(0.7),
    limit: int = Body(5),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Find response examples similar to a given fan message"""
    
    try:
        # Generate embedding using OpenAI
        embedding_response = await ai_service.client.embeddings.create(
            model="text-embedding-ada-002",
            input=fan_message
        )
        embedding = embedding_response.data[0].embedding
        
        # Find similar examples
        similar_examples = await vector_service.find_similar_response_examples(
            creator_id=creator_id,
            embedding=embedding,
            similarity_threshold=similarity_threshold,
            limit=limit,
            category=category
        )
        
        # Convert to clean response models
        clean_examples = []
        for example, _ in similar_examples:
            clean_responses = []
            if example.responses:
                for resp in example.responses:
                    clean_responses.append(CreatorResponseResponse(
                        id=resp.id,
                        example_id=resp.example_id,
                        response_text=resp.response_text,
                        ranking=resp.ranking
                    ))
            
            clean_examples.append(ResponseExampleResponse(
                id=example.id,
                creator_id=example.creator_id,
                fan_message=example.fan_message,
                category=example.category,
                created_at=example.created_at.isoformat(),
                updated_at=example.updated_at.isoformat(),
                responses=clean_responses
            ))
        
        return clean_examples
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding similar examples: {str(e)}"
        )

# Bulk operations
@router.post("/{creator_id}/bulk-style-examples", status_code=status.HTTP_201_CREATED)
async def bulk_create_style_examples(
    creator_id: int,
    examples: List[StyleExampleCreate],
    admin_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Create multiple style examples in bulk"""
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    created_count = 0
    errors = []
    
    for idx, example in enumerate(examples):
        try:
            # Generate embedding
            embedding_response = await ai_service.client.embeddings.create(
                model="text-embedding-ada-002",
                input=example.fan_message
            )
            embedding = embedding_response.data[0].embedding
            
            # Store example
            await vector_service.store_style_example(
                creator_id=creator_id,
                fan_message=example.fan_message,
                creator_response=example.creator_response,
                category=example.category,
                embedding=embedding
            )
            
            created_count += 1
            
        except Exception as e:
            errors.append({
                "index": idx,
                "fan_message": example.fan_message[:50] + "...",
                "error": str(e)
            })
    
    return {
        "success": True,
        "created_count": created_count,
        "total_count": len(examples),
        "errors": errors if errors else None
    }

@router.post("/{creator_id}/bulk-response-examples", status_code=status.HTTP_201_CREATED)
async def bulk_create_response_examples(
    creator_id: int,
    examples: List[ResponseExampleCreate],
    admin_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Create multiple response examples in bulk"""
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    created_count = 0
    errors = []
    
    for idx, example in enumerate(examples):
        try:
            # Check if we have at least one response
            if not example.responses or len(example.responses) == 0:
                raise ValueError("At least one response is required")
            
            # Generate embedding
            embedding_response = await ai_service.client.embeddings.create(
                model="text-embedding-ada-002",
                input=example.fan_message
            )
            embedding = embedding_response.data[0].embedding
            
            # Extract response texts and rankings
            response_texts = [resp.response_text for resp in example.responses]
            rankings = [resp.ranking for resp in example.responses if resp.ranking is not None]
            
            # Store example
            await vector_service.store_response_example(
                creator_id=creator_id,
                fan_message=example.fan_message,
                responses=response_texts,
                rankings=rankings if rankings else None,
                category=example.category,
                embedding=embedding
            )
            
            created_count += 1
            
        except Exception as e:
            errors.append({
                "index": idx,
                "fan_message": example.fan_message[:50] + "...",
                "error": str(e)
            })
    
    return {
        "success": True,
        "created_count": created_count,
        "total_count": len(examples),
        "errors": errors if errors else None
    }