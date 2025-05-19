# File: app/api/dependencies.py (updated)
# Path: fanfix-api/app/api/dependencies.py

from fastapi import Depends, HTTPException, status
from app.auth.users import current_active_user, get_prisma
from app.auth.models import User
from prisma import Prisma
from typing import Dict, Any

# Check if user has API key set
async def require_api_key(
    current_user: User = Depends(current_active_user),
    prisma: Prisma = Depends(get_prisma)
) -> Dict[str, Any]:
    """
    Checks if the user has configured an OpenAI API key.
    Returns the user preferences if the API key exists.
    """
    user_prefs = await prisma.userpreferences.find_unique(
        where={"userId": str(current_user.id)}
    )
    
    if not user_prefs or not user_prefs.openaiApiKey:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OpenAI API key not configured. Please update your preferences."
        )
    
    return user_prefs

# Dependency for pagination
def pagination_params(
    page: int = 1,
    page_size: int = 10,
    max_page_size: int = 100
) -> Dict[str, Any]:
    """
    Provides pagination parameters for database queries.
    Returns a dictionary with skip, take, page, and page_size.
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > max_page_size:
        page_size = max_page_size
        
    # Calculate skip value for database query
    skip = (page - 1) * page_size
    
    return {
        "skip": skip,
        "take": page_size,
        "page": page,
        "page_size": page_size
    }

# Check if user is a creator manager (admin)
async def require_creator_manager(
    current_user: User = Depends(current_active_user)
) -> User:
    """
    Checks if the user has permission to manage creators (admin).
    Returns the current user if they have sufficient permissions.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage creators"
        )
    return current_user