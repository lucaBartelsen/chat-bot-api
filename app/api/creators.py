# File: app/api/creators.py (updated)
# Path: fanfix-api/app/api/creators.py

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
import uuid

from prisma import Prisma
from app.auth.models import User
from app.auth.users import current_active_user, get_prisma
from app.api.dependencies import require_creator_manager, pagination_params
from app.models.creator import (
    CreatorCreate,
    CreatorRead,
    CreatorUpdate,
    CreatorStyleCreate,
    CreatorStyleRead,
    CreatorStyleUpdate,
    StyleExampleCreate,
    StyleExampleRead
)

router = APIRouter(prefix="/creators", tags=["creators"])

@router.get("/", response_model=List[CreatorRead])
async def get_all_creators(
    active_only: bool = True,
    pagination: dict = Depends(pagination_params),
    current_user: User = Depends(current_active_user),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Get all creators, filtered by active status if specified
    """
    where_condition = {"active": True} if active_only else {}
    
    creators = await prisma.creator.find_many(
        where=where_condition,
        skip=pagination["skip"],
        take=pagination["take"],
        order_by={"name": "asc"}
    )
        
    return creators

@router.get("/{creator_id}", response_model=CreatorRead)
async def get_creator_by_id(
    creator_id: uuid.UUID,
    current_user: User = Depends(current_active_user),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Get a specific creator by ID
    """
    creator = await prisma.creator.find_unique(
        where={"id": str(creator_id)},
        include={
            "style": True,
            "examples": {
                "take": 5,
                "order_by": {"createdAt": "desc"}
            }
        }
    )
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creator not found"
        )
        
    return creator

@router.post("/", response_model=CreatorRead)
async def create_creator(
    creator_in: CreatorCreate,
    current_user: User = Depends(require_creator_manager),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Create a new creator (admin only)
    """
    creator = await prisma.creator.create(
        data={
            "name": creator_in.name,
            "description": creator_in.description,
            "avatarUrl": creator_in.avatar_url,
            "active": creator_in.active
        }
    )
    
    return creator

@router.patch("/{creator_id}", response_model=CreatorRead)
async def update_creator(
    creator_id: uuid.UUID,
    creator_in: CreatorUpdate,
    current_user: User = Depends(require_creator_manager),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Update an existing creator (admin only)
    """
    # Check if creator exists
    creator = await prisma.creator.find_unique(
        where={"id": str(creator_id)}
    )
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creator not found"
        )
    
    # Update creator
    update_data = {}
    if creator_in.name is not None:
        update_data["name"] = creator_in.name
    if creator_in.description is not None:
        update_data["description"] = creator_in.description
    if creator_in.avatar_url is not None:
        update_data["avatarUrl"] = creator_in.avatar_url
    if creator_in.active is not None:
        update_data["active"] = creator_in.active
        
    creator = await prisma.creator.update(
        where={"id": str(creator_id)},
        data=update_data
    )
    
    return creator

@router.post("/{creator_id}/style", response_model=CreatorStyleRead)
async def create_or_update_style(
    creator_id: uuid.UUID,
    style_in: CreatorStyleCreate,
    current_user: User = Depends(require_creator_manager),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Create or update a creator's writing style (admin only)
    """
    # Check if creator exists
    creator = await prisma.creator.find_unique(
        where={"id": str(creator_id)}
    )
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creator not found"
        )
    
    # Check if style already exists
    existing_style = await prisma.creatorstyle.find_unique(
        where={"creatorId": str(creator_id)}
    )
    
    if existing_style:
        # Update existing style
        style = await prisma.creatorstyle.update(
            where={"creatorId": str(creator_id)},
            data={
                "approvedEmojis": style_in.approved_emojis,
                "caseStyle": style_in.case_style,
                "textReplacements": style_in.text_replacements,
                "sentenceSeparators": style_in.sentence_separators,
                "punctuationRules": style_in.punctuation_rules,
                "abbreviations": style_in.abbreviations,
                "messageLengthPreference": style_in.message_length_preference,
                "styleInstructions": style_in.style_instructions,
                "toneRange": style_in.tone_range
            }
        )
    else:
        # Create new style
        style = await prisma.creatorstyle.create(
            data={
                "creatorId": str(creator_id),
                "approvedEmojis": style_in.approved_emojis,
                "caseStyle": style_in.case_style,
                "textReplacements": style_in.text_replacements,
                "sentenceSeparators": style_in.sentence_separators,
                "punctuationRules": style_in.punctuation_rules,
                "abbreviations": style_in.abbreviations,
                "messageLengthPreference": style_in.message_length_preference,
                "styleInstructions": style_in.style_instructions,
                "toneRange": style_in.tone_range
            }
        )
    
    return style

@router.post("/{creator_id}/examples", response_model=StyleExampleRead)
async def add_style_example(
    creator_id: uuid.UUID,
    example_in: StyleExampleCreate,
    current_user: User = Depends(require_creator_manager),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Add a new style example for a creator (admin only)
    """
    # Check if creator exists
    creator = await prisma.creator.find_unique(
        where={"id": str(creator_id)}
    )
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creator not found"
        )
    
    # Create new example
    example = await prisma.styleexample.create(
        data={
            "creatorId": str(creator_id),
            "fanMessage": example_in.fan_message,
            "creatorResponses": example_in.creator_responses
        }
    )
    
    return example

@router.get("/{creator_id}/examples", response_model=List[StyleExampleRead])
async def get_style_examples(
    creator_id: uuid.UUID,
    pagination: dict = Depends(pagination_params),
    current_user: User = Depends(current_active_user),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Get style examples for a creator
    """
    # Check if creator exists
    creator = await prisma.creator.find_unique(
        where={"id": str(creator_id)}
    )
    
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creator not found"
        )
    
    examples = await prisma.styleexample.find_many(
        where={"creatorId": str(creator_id)},
        skip=pagination["skip"],
        take=pagination["take"],
        order_by={"createdAt": "desc"}
    )
    
    return examples

@router.delete("/{creator_id}/examples/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style_example(
    creator_id: uuid.UUID,
    example_id: uuid.UUID,
    current_user: User = Depends(require_creator_manager),
    prisma: Prisma = Depends(get_prisma)
) -> Any:
    """
    Delete a style example (admin only)
    """
    # Check if example exists
    example = await prisma.styleexample.find_first(
        where={
            "id": str(example_id),
            "creatorId": str(creator_id)
        }
    )
    
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found"
        )
    
    # Delete example
    await prisma.styleexample.delete(
        where={"id": str(example_id)}
    )
    
    return None