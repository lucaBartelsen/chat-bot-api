# File: app/auth/router.py (updated)
# Path: fanfix-api/app/auth/router.py

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from prisma import Prisma
import uuid

from app.auth.users import (
    fastapi_users,
    auth_backend,
    current_active_user,
    get_prisma
)
from app.auth.models import (
    User,
    UserPreferencesRead,
    UserPreferencesUpdate
)

# Create the auth router
router = APIRouter(prefix="/auth", tags=["auth"])

# Include FastAPI Users routers
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
)

# Import user schemas for router registration
from app.auth.models import User, UserCreate, UserUpdate

# Explicitly set documentation paths
router.include_router(
    fastapi_users.get_register_router(User, UserCreate),
    prefix="",
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="",
)

router.include_router(
    fastapi_users.get_verify_router(User),
    prefix="",
)

router.include_router(
    fastapi_users.get_users_router(User, UserUpdate),
    prefix="",
)

# Custom user routes
@router.get("/me/preferences", response_model=UserPreferencesRead)
async def get_preferences(
    current_user: User = Depends(current_active_user),
    prisma: Prisma = Depends(get_prisma)
) -> UserPreferencesRead:
    """
    Get user preferences
    """
    preferences = await prisma.userpreferences.find_unique(
        where={"userId": str(current_user.id)}
    )
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
    
    # Handle potential None values
    selected_creator_id = None
    if preferences.selectedCreatorId:
        try:
            selected_creator_id = uuid.UUID(preferences.selectedCreatorId)
        except (ValueError, TypeError):
            selected_creator_id = None
    
    return UserPreferencesRead(
        user_id=current_user.id,
        selected_creator_id=selected_creator_id,
        openai_api_key=preferences.openaiApiKey,
        model_name=preferences.modelName,
        num_suggestions=preferences.numSuggestions
    )

@router.patch("/me/preferences", response_model=UserPreferencesRead)
async def update_preferences(
    preferences_in: UserPreferencesUpdate,
    current_user: User = Depends(current_active_user),
    prisma: Prisma = Depends(get_prisma)
) -> UserPreferencesRead:
    """
    Update user preferences
    """
    preferences = await prisma.userpreferences.find_unique(
        where={"userId": str(current_user.id)}
    )
    
    if not preferences:
        # Create preferences if they don't exist
        preferences = await prisma.userpreferences.create(
            data={
                "userId": str(current_user.id),
                "selectedCreatorId": str(preferences_in.selected_creator_id) if preferences_in.selected_creator_id else None,
                "openaiApiKey": preferences_in.openai_api_key,
                "modelName": preferences_in.model_name or "gpt-3.5-turbo",
                "numSuggestions": preferences_in.num_suggestions or 3
            }
        )
    else:
        # Update existing preferences
        update_data = {}
        if preferences_in.selected_creator_id is not None:
            update_data["selectedCreatorId"] = str(preferences_in.selected_creator_id)
        if preferences_in.openai_api_key is not None:
            update_data["openaiApiKey"] = preferences_in.openai_api_key
        if preferences_in.model_name is not None:
            update_data["modelName"] = preferences_in.model_name
        if preferences_in.num_suggestions is not None:
            update_data["numSuggestions"] = preferences_in.num_suggestions
            
        preferences = await prisma.userpreferences.update(
            where={"userId": str(current_user.id)},
            data=update_data
        )
    
    # Handle potential None values
    selected_creator_id = None
    if preferences.selectedCreatorId:
        try:
            selected_creator_id = uuid.UUID(preferences.selectedCreatorId)
        except (ValueError, TypeError):
            selected_creator_id = None
    
    return UserPreferencesRead(
        user_id=current_user.id,
        selected_creator_id=selected_creator_id,
        openai_api_key=preferences.openaiApiKey,
        model_name=preferences.modelName,
        num_suggestions=preferences.numSuggestions
    )

@router.post("/me/update-last-login", status_code=status.HTTP_200_OK)
async def update_last_login(
    current_user: User = Depends(current_active_user),
    prisma: Prisma = Depends(get_prisma)
):
    """
    Update the user's last login timestamp
    """
    await prisma.user.update(
        where={"id": str(current_user.id)},
        data={"lastLogin": datetime.now()}
    )
    return {"status": "success"}