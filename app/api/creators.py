# app/api/creators.py - Updated to auto-create style config on creator creation

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from pydantic import BaseModel

from app.core.database import get_session
from app.models.creator import Creator, CreatorStyle, StyleExample
from app.auth.users import get_current_active_user
from app.models.user import User

router = APIRouter()

# Clean response models (no embeddings to avoid numpy serialization issues)
class StyleExampleResponse(BaseModel):
    """Response model for style examples - excludes embedding field"""
    id: int
    creator_id: int
    fan_message: str
    creator_response: str
    category: Optional[str] = None
    created_at: str  # Use string for datetime to avoid serialization issues
    updated_at: str

class StyleExamplesResponse(BaseModel):
    items: List[StyleExampleResponse]
    total: int
    page: int
    size: int
    pages: int

class CreatorsResponse(BaseModel):
    items: List[Creator]
    total: int
    page: int
    size: int
    pages: int

def create_default_style_config(creator_id: int) -> CreatorStyle:
    """Create a default style configuration for a new creator"""
    return CreatorStyle(
        creator_id=creator_id,
        # Basic text styling defaults
        case_style="sentence",  # Most natural for conversation
        approved_emojis=["😊", "❤️", "😘", "😉", "👋", "🔥", "💕", "😍", "🥰", "💋"],  # Common friendly emojis
        sentence_separators=[".", "!", "?"],  # Standard punctuation
        
        # Text replacements - common casual conversions
        text_replacements={
            "you": "u",
            "your": "ur", 
            "because": "bc",
            "probably": "prob",
            "definitely": "def"
        },
        
        # Common abbreviations
        common_abbreviations={
            "btw": "by the way",
            "omg": "oh my god", 
            "lol": "laugh out loud",
            "tbh": "to be honest",
            "imo": "in my opinion",
            "rn": "right now",
            "ngl": "not gonna lie"
        },
        
        # Message length preferences
        message_length_preferences={
            "min_length": 10,
            "max_length": 500,
            "optimal_length": 150
        },
        
        # Punctuation rules
        punctuation_rules={
            "use_ellipsis": True,
            "use_exclamations": True, 
            "max_consecutive_exclamations": 2
        },
        
        # Default style instructions
        style_instructions="""Write in a friendly, conversational tone. Keep messages engaging and personal. Use casual language that feels natural and authentic. Vary your responses to avoid sounding repetitive.""",
        
        # Default tone range
        tone_range=["friendly", "casual", "enthusiastic", "supportive", "playful"]
    )

# CREATORS CRUD ENDPOINTS
@router.get("/", response_model=CreatorsResponse)
@router.get("", response_model=CreatorsResponse)
async def list_creators(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
):
    """List all creators with pagination"""
    
    # Get total count
    count_query = select(func.count(Creator.id))
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0
    
    # Get paginated results
    query = select(Creator).offset(skip).limit(limit).order_by(Creator.created_at.desc())
    result = await session.execute(query)
    creators = result.scalars().all()
    
    # Calculate pagination info
    pages = max(1, (total + limit - 1) // limit)
    current_page = (skip // limit) + 1
    
    return CreatorsResponse(
        items=creators,
        total=total,
        page=current_page,
        size=limit,
        pages=pages
    )

@router.get("/{creator_id}", response_model=Creator)
async def get_creator(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get creator details by ID"""
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    return creator

@router.post("/", response_model=Creator, status_code=status.HTTP_201_CREATED)
async def create_creator(
    creator: Creator,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new creator with default style configuration"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create creators",
        )
    
    # Add creator to database
    session.add(creator)
    await session.flush()  # Get the creator ID without committing
    
    # Create default style configuration
    default_style = create_default_style_config(creator.id)
    session.add(default_style)
    
    # Commit both creator and style config
    await session.commit()
    await session.refresh(creator)
    
    print(f"✅ Created creator '{creator.name}' (ID: {creator.id}) with default style configuration")
    
    return creator

@router.patch("/{creator_id}", response_model=Creator)
async def update_creator(
    creator_id: int,
    creator_update: Creator,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Update creator information"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update creators",
        )
    
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    db_creator = result.scalar_one_or_none()
    
    if not db_creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    # Update creator attributes
    for key, value in creator_update.model_dump(exclude_unset=True).items():
        setattr(db_creator, key, value)
    
    await session.commit()
    await session.refresh(db_creator)
    return db_creator

@router.delete("/{creator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_creator(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a creator"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete creators",
        )
    
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    await session.delete(creator)
    await session.commit()
    return None

# CREATOR STYLE ENDPOINTS
@router.get("/{creator_id}/style", response_model=CreatorStyle)
async def get_creator_style(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get creator's writing style configuration"""
    # First check if creator exists
    creator_query = select(Creator).where(Creator.id == creator_id)
    creator_result = await session.execute(creator_query)
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    # Get creator style
    style_query = select(CreatorStyle).where(CreatorStyle.creator_id == creator_id)
    style_result = await session.execute(style_query)
    style = style_result.scalar_one_or_none()
    
    if not style:
        # This shouldn't happen with the new auto-creation, but let's handle it gracefully
        # Create default style configuration if missing
        style = create_default_style_config(creator_id)
        session.add(style)
        await session.commit()
        await session.refresh(style)
        print(f"⚠️ Created missing style config for creator {creator_id}")
    
    return style

@router.post("/{creator_id}/style", response_model=CreatorStyle)
async def store_creator_style(
    creator_id: int,
    style: CreatorStyle,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Store a creator's writing style (use PATCH to update existing)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify creator styles",
        )
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    # Check if style already exists
    existing_style_query = select(CreatorStyle).where(CreatorStyle.creator_id == creator_id)
    existing_style_result = await session.execute(existing_style_query)
    existing_style = existing_style_result.scalar_one_or_none()
    
    if existing_style:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Style already exists for creator {creator_id}. Use PATCH to update.",
        )
    
    # Set creator_id
    style.creator_id = creator_id
    
    # Add style to db
    session.add(style)
    await session.commit()
    await session.refresh(style)
    
    return style

@router.patch("/{creator_id}/style", response_model=CreatorStyle)
async def update_creator_style(
    creator_id: int,
    style_update: CreatorStyle,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Update a creator's writing style"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify creator styles",
        )
    
    # Check if creator exists
    creator_query = select(Creator).where(Creator.id == creator_id)
    creator_result = await session.execute(creator_query)
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    # Get existing style
    style_query = select(CreatorStyle).where(CreatorStyle.creator_id == creator_id)
    style_result = await session.execute(style_query)
    existing_style = style_result.scalar_one_or_none()
    
    if not existing_style:
        # Create default style if missing (shouldn't happen with auto-creation)
        existing_style = create_default_style_config(creator_id)
        session.add(existing_style)
        await session.flush()
        print(f"⚠️ Created missing style config during update for creator {creator_id}")
    
    # Update style attributes
    for key, value in style_update.model_dump(exclude_unset=True).items():
        if key != "creator_id":  # Prevent changing creator_id
            setattr(existing_style, key, value)
    
    await session.commit()
    await session.refresh(existing_style)
    
    return existing_style

@router.delete("/{creator_id}/style", status_code=status.HTTP_204_NO_CONTENT)
async def delete_creator_style(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a creator's writing style (will recreate default on next access)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify creator styles",
        )
    
    # Get existing style
    style_query = select(CreatorStyle).where(CreatorStyle.creator_id == creator_id)
    style_result = await session.execute(style_query)
    existing_style = style_result.scalar_one_or_none()
    
    if not existing_style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Style configuration not found for creator {creator_id}",
        )
    
    await session.delete(existing_style)
    await session.commit()
    
    return None

# STYLE EXAMPLES ENDPOINTS
@router.get("/{creator_id}/style-examples", response_model=StyleExamplesResponse)
async def get_style_examples(
    creator_id: int,
    category: Optional[str] = Query(None, description="Filter by category ('all' for no filter)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in fan_message and creator_response"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get style examples for a creator with pagination, search, and filtering"""
    
    # Check if creator exists
    creator_query = select(Creator).where(Creator.id == creator_id)
    creator_result = await session.execute(creator_query)
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    # Build base query
    base_query = select(StyleExample).where(StyleExample.creator_id == creator_id)
    
    # Add search filter
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        search_filter = (
            StyleExample.fan_message.ilike(search_term) | 
            StyleExample.creator_response.ilike(search_term)
        )
        base_query = base_query.where(search_filter)
    
    # Add category filter
    if category and category != 'all' and category.strip():
        base_query = base_query.where(StyleExample.category == category)
    
    # Get total count for pagination
    count_stmt = select(func.count()).select_from(
        base_query.subquery()
    )
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # Get paginated results, ordered by creation date (newest first)
    paginated_query = (
        base_query
        .order_by(StyleExample.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await session.execute(paginated_query)
    examples = result.scalars().all()
    
    # Calculate pagination metadata
    pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
    current_page = (skip // limit) + 1
    
    # Convert to clean response models without embeddings
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
    
    return StyleExamplesResponse(
        items=clean_examples,
        total=total,
        page=current_page,
        size=limit,
        pages=pages
    )

# Basic CRUD for style examples (No AI features) - Using clean response model
@router.post("/{creator_id}/examples", response_model=StyleExampleResponse, status_code=status.HTTP_201_CREATED)
async def add_basic_style_example(
    creator_id: int,
    example: StyleExample,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Add a basic style example (without AI embedding) - Use /api/creators/{id}/style-examples for AI features"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add style examples",
        )
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    # Set creator_id
    example.creator_id = creator_id
    
    # Add example to db (no embedding generation)
    session.add(example)
    await session.commit()
    await session.refresh(example)
    
    # Return clean response model
    return StyleExampleResponse(
        id=example.id,
        creator_id=example.creator_id,
        fan_message=example.fan_message,
        creator_response=example.creator_response,
        category=example.category,
        created_at=example.created_at.isoformat(),
        updated_at=example.updated_at.isoformat()
    )

@router.get("/{creator_id}/examples", response_model=List[StyleExampleResponse])
async def get_creator_examples(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """Get basic style examples for a creator (legacy endpoint)"""
    query = select(StyleExample).where(StyleExample.creator_id == creator_id).offset(skip).limit(limit)
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

@router.patch("/{creator_id}/examples/{example_id}", response_model=StyleExampleResponse)
async def update_style_example(
    creator_id: int,
    example_id: int,
    example_update: StyleExample,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Update a basic style example"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update style examples",
        )
    
    # Get existing example
    query = select(StyleExample).where(
        StyleExample.id == example_id,
        StyleExample.creator_id == creator_id
    )
    result = await session.execute(query)
    existing_example = result.scalar_one_or_none()
    
    if not existing_example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Style example with ID {example_id} not found for creator {creator_id}",
        )
    
    # Update example attributes
    for key, value in example_update.model_dump(exclude_unset=True).items():
        if key not in ["id", "creator_id", "created_at", "updated_at"]:  # Prevent changing these fields
            setattr(existing_example, key, value)
    
    await session.commit()
    await session.refresh(existing_example)
    
    # Return clean response model
    return StyleExampleResponse(
        id=existing_example.id,
        creator_id=existing_example.creator_id,
        fan_message=existing_example.fan_message,
        creator_response=existing_example.creator_response,
        category=existing_example.category,
        created_at=existing_example.created_at.isoformat(),
        updated_at=existing_example.updated_at.isoformat()
    )

@router.delete("/{creator_id}/examples/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_basic_style_example(
    creator_id: int,
    example_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a basic style example"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete style examples",
        )
    
    # Get existing example
    query = select(StyleExample).where(
        StyleExample.id == example_id,
        StyleExample.creator_id == creator_id
    )
    result = await session.execute(query)
    existing_example = result.scalar_one_or_none()
    
    if not existing_example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Style example with ID {example_id} not found for creator {creator_id}",
        )
    
    await session.delete(existing_example)
    await session.commit()
    
    return None

# UTILITY ENDPOINTS
@router.get("/{creator_id}/statistics")
async def get_creator_statistics(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get statistics for a specific creator"""
    
    # Check if creator exists
    creator_query = select(Creator).where(Creator.id == creator_id)
    creator_result = await session.execute(creator_query)
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    # Count style examples
    style_count_query = select(func.count(StyleExample.id)).where(StyleExample.creator_id == creator_id)
    style_count_result = await session.execute(style_count_query)
    style_count = style_count_result.scalar() or 0
    
    # Count style examples by category
    style_by_category_query = select(
        StyleExample.category,
        func.count(StyleExample.id).label('count')
    ).where(
        StyleExample.creator_id == creator_id,
        StyleExample.category.is_not(None)
    ).group_by(StyleExample.category)
    
    style_by_category_result = await session.execute(style_by_category_query)
    style_by_category = {row[0]: row[1] for row in style_by_category_result.all()}
    
    # Get recent examples
    recent_examples_query = select(StyleExample).where(
        StyleExample.creator_id == creator_id
    ).order_by(StyleExample.created_at.desc()).limit(5)
    
    recent_examples_result = await session.execute(recent_examples_query)
    recent_examples = recent_examples_result.scalars().all()
    
    # Check if creator has style config
    style_query = select(CreatorStyle).where(CreatorStyle.creator_id == creator_id)
    style_result = await session.execute(style_query)
    has_style_config = style_result.scalar_one_or_none() is not None
    
    return {
        "creator_id": creator_id,
        "creator_name": creator.name,
        "creator_active": creator.is_active,
        "style_examples_count": style_count,
        "style_examples_by_category": style_by_category,
        "recent_examples": [
            {
                "id": ex.id,
                "fan_message": ex.fan_message[:100] + "..." if len(ex.fan_message) > 100 else ex.fan_message,
                "category": ex.category,
                "created_at": ex.created_at.isoformat()
            }
            for ex in recent_examples
        ],
        "has_style_config": has_style_config
    }

@router.get("/{creator_id}/categories")
async def get_creator_categories(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get all categories used by a creator"""
    
    # Check if creator exists
    creator_query = select(Creator).where(Creator.id == creator_id)
    creator_result = await session.execute(creator_query)
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    # Get unique categories for style examples
    categories_query = select(StyleExample.category).where(
        StyleExample.creator_id == creator_id,
        StyleExample.category.is_not(None)
    ).distinct()
    
    categories_result = await session.execute(categories_query)
    categories = [row[0] for row in categories_result.all()]
    
    # Count examples per category
    category_counts = {}
    for category in categories:
        count_query = select(func.count(StyleExample.id)).where(
            StyleExample.creator_id == creator_id,
            StyleExample.category == category
        )
        count_result = await session.execute(count_query)
        category_counts[category] = count_result.scalar() or 0
    
    return {
        "creator_id": creator_id,
        "categories": categories,
        "category_counts": category_counts,
        "total_categories": len(categories)
    }

@router.post("/{creator_id}/activate", response_model=Creator)
async def activate_creator(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Activate a creator"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to activate creators",
        )
    
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    creator.is_active = True
    await session.commit()
    await session.refresh(creator)
    
    return creator

@router.post("/{creator_id}/deactivate", response_model=Creator)
async def deactivate_creator(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Deactivate a creator"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deactivate creators",
        )
    
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.execute(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    creator.is_active = False
    await session.commit()
    await session.refresh(creator)
    
    return creator

@router.get("/{creator_id}/stats", response_model=Dict[str, Any])
async def get_creator_statistics(
    creator_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get comprehensive statistics for a specific creator"""
    
    # Check if creator exists
    creator_query = select(Creator).where(Creator.id == creator_id)
    creator_result = await session.execute(creator_query)
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found"
        )
    
    # Count style examples
    style_count_query = select(func.count(StyleExample.id)).where(StyleExample.creator_id == creator_id)
    style_count_result = await session.execute(style_count_query)
    style_examples_count = style_count_result.scalar() or 0
    
    # Count response examples - WICHTIG: Das ist der fehlende Teil!
    from app.models.creator import ResponseExample
    response_count_query = select(func.count(ResponseExample.id)).where(ResponseExample.creator_id == creator_id)
    response_count_result = await session.execute(response_count_query)
    response_examples_count = response_count_result.scalar() or 0
    
    # Count individual responses (total responses across all examples)
    from app.models.creator import CreatorResponse
    individual_responses_query = select(func.count(CreatorResponse.id)).join(
        ResponseExample, CreatorResponse.example_id == ResponseExample.id
    ).where(ResponseExample.creator_id == creator_id)
    individual_responses_result = await session.execute(individual_responses_query)
    total_individual_responses = individual_responses_result.scalar() or 0
    
    # Count vector store conversations (if available)
    try:
        from app.models.creator import VectorStore
        vector_count_query = select(func.count(VectorStore.id)).where(VectorStore.creator_id == creator_id)
        vector_count_result = await session.execute(vector_count_query)
        conversation_count = vector_count_result.scalar() or 0
    except ImportError:
        conversation_count = 0
    
    # Get style examples by category
    style_by_category_query = select(
        StyleExample.category,
        func.count(StyleExample.id).label('count')
    ).where(
        StyleExample.creator_id == creator_id,
        StyleExample.category.is_not(None)
    ).group_by(StyleExample.category)
    
    style_by_category_result = await session.execute(style_by_category_query)
    style_by_category = {row[0]: row[1] for row in style_by_category_result.all()}
    
    # Get response examples by category
    response_by_category_query = select(
        ResponseExample.category,
        func.count(ResponseExample.id).label('count')
    ).where(
        ResponseExample.creator_id == creator_id,
        ResponseExample.category.is_not(None)
    ).group_by(ResponseExample.category)
    
    response_by_category_result = await session.execute(response_by_category_query)
    response_by_category = {row[0]: row[1] for row in response_by_category_result.all()}
    
    # Get recent examples (last 5)
    recent_style_examples_query = select(StyleExample).where(
        StyleExample.creator_id == creator_id
    ).order_by(StyleExample.created_at.desc()).limit(5)
    
    recent_style_result = await session.execute(recent_style_examples_query)
    recent_style_examples = recent_style_result.scalars().all()
    
    # Check if creator has style config
    style_config_query = select(CreatorStyle).where(CreatorStyle.creator_id == creator_id)
    style_config_result = await session.execute(style_config_query)
    has_style_config = style_config_result.scalar_one_or_none() is not None
    
    # Calculate total examples
    total_examples = style_examples_count + response_examples_count
    
    return {
        "creator_id": creator_id,
        "creator_name": creator.name,
        "creator_active": creator.is_active,
        "creator_description": creator.description,
        
        # Main counts - This is what the frontend needs!
        "style_examples_count": style_examples_count,
        "response_examples_count": response_examples_count,
        "total_individual_responses": total_individual_responses,
        "total_examples": total_examples,
        "conversation_count": conversation_count,
        
        # Category breakdowns
        "style_examples_by_category": style_by_category,
        "response_examples_by_category": response_by_category,
        
        # Recent activity
        "recent_examples": [
            {
                "id": ex.id,
                "fan_message": ex.fan_message[:100] + "..." if len(ex.fan_message) > 100 else ex.fan_message,
                "category": ex.category,
                "created_at": ex.created_at.isoformat()
            }
            for ex in recent_style_examples
        ],
        
        # Configuration status
        "has_style_config": has_style_config,
        
        # Timestamps
        "created_at": creator.created_at.isoformat(),
        "updated_at": creator.updated_at.isoformat(),
        "stats_generated_at": datetime.utcnow().isoformat()
    }


# Alternative: Bulk stats endpoint for multiple creators (more efficient for overview page)
@router.post("/bulk-stats", response_model=Dict[int, Dict[str, Any]])
async def get_bulk_creator_statistics(
    creator_ids: List[int] = Body(..., description="List of creator IDs to get stats for"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get statistics for multiple creators in one request (more efficient for overview page)"""
    
    if not creator_ids or len(creator_ids) > 50:  # Limit to prevent abuse
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide 1-50 creator IDs"
        )
    
    # Verify all creators exist
    creators_query = select(Creator).where(Creator.id.in_(creator_ids))
    creators_result = await session.execute(creators_query)
    creators = {c.id: c for c in creators_result.scalars().all()}
    
    if len(creators) != len(creator_ids):
        missing_ids = set(creator_ids) - set(creators.keys())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creators not found: {list(missing_ids)}"
        )
    
    # Bulk count style examples
    style_counts_query = select(
        StyleExample.creator_id,
        func.count(StyleExample.id).label('count')
    ).where(
        StyleExample.creator_id.in_(creator_ids)
    ).group_by(StyleExample.creator_id)
    
    style_counts_result = await session.execute(style_counts_query)
    style_counts = {row[0]: row[1] for row in style_counts_result.all()}
    
    # Bulk count response examples
    from app.models.creator import ResponseExample
    response_counts_query = select(
        ResponseExample.creator_id,
        func.count(ResponseExample.id).label('count')
    ).where(
        ResponseExample.creator_id.in_(creator_ids)
    ).group_by(ResponseExample.creator_id)
    
    response_counts_result = await session.execute(response_counts_query)
    response_counts = {row[0]: row[1] for row in response_counts_result.all()}
    
    # Build response
    stats_map = {}
    for creator_id in creator_ids:
        creator = creators[creator_id]
        style_count = style_counts.get(creator_id, 0)
        response_count = response_counts.get(creator_id, 0)
        
        stats_map[creator_id] = {
            "creator_id": creator_id,
            "creator_name": creator.name,
            "creator_active": creator.is_active,
            "style_examples_count": style_count,
            "response_examples_count": response_count,
            "total_examples": style_count + response_count,
            "created_at": creator.created_at.isoformat(),
            "updated_at": creator.updated_at.isoformat()
        }
    
    return stats_map