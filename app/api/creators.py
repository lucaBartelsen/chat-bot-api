from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.creator import Creator, CreatorStyle, StyleExample
from app.auth.users import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Creator])
async def list_creators(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all creators"""
    query = select(Creator).offset(skip).limit(limit)
    result = await session.exec(query)
    return result.scalars().all()

@router.get("/{creator_id}", response_model=Creator)
async def get_creator(
    creator_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get creator details by ID"""
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.exec(query)
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
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new creator"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create creators",
        )
    
    session.add(creator)
    await session.commit()
    await session.refresh(creator)
    return creator

@router.patch("/{creator_id}", response_model=Creator)
async def update_creator(
    creator_id: int,
    creator_update: Creator,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Update creator information"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update creators",
        )
    
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.exec(query)
    db_creator = result.scalar_one_or_none()
    
    if not db_creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    # Update creator attributes
    # Updated for Pydantic v2: dict() -> model_dump()
    for key, value in creator_update.model_dump(exclude_unset=True).items():
        setattr(db_creator, key, value)
    
    await session.commit()
    await session.refresh(db_creator)
    return db_creator

@router.post("/{creator_id}/style", response_model=CreatorStyle)
async def store_creator_style(
    creator_id: int,
    style: CreatorStyle,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Store a creator's writing style"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify creator styles",
        )
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.exec(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    # Set creator_id
    style.creator_id = creator_id
    
    # Add style to db
    session.add(style)
    await session.commit()
    await session.refresh(style)
    
    return style

@router.post("/{creator_id}/examples", response_model=StyleExample)
async def add_style_example(
    creator_id: int,
    example: StyleExample,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Add a style example for a creator"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add style examples",
        )
    
    # Check if creator exists
    query = select(Creator).where(Creator.id == creator_id)
    result = await session.exec(query)
    creator = result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator with ID {creator_id} not found",
        )
    
    # Set creator_id
    example.creator_id = creator_id
    
    # Add example to db
    session.add(example)
    await session.commit()
    await session.refresh(example)
    
    return example

@router.get("/{creator_id}/examples", response_model=List[StyleExample])
async def get_creator_examples(
    creator_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """Get style examples for a creator"""
    query = select(StyleExample).where(StyleExample.creator_id == creator_id).offset(skip).limit(limit)
    result = await session.exec(query)
    return result.scalars().all()