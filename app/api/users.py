# app/api/users.py - Complete user management API

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.core.database import get_session
from app.models.user import User, UserPreference
from app.core.security import get_password_hash, verify_password
from app.auth.users import get_current_active_user, get_current_admin_user

router = APIRouter()

# Request/Response models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    is_admin: bool = False
    is_active: bool = True
    openai_api_key: Optional[str] = None
    default_model: str = "gpt-4"
    suggestion_count: int = Field(default=3, ge=1, le=10)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

class UserWithPreferencesResponse(UserResponse):
    preferences: Optional['UserPreferenceResponse'] = None

class UserPreferenceResponse(BaseModel):
    id: int
    user_id: int
    openai_api_key: Optional[str] = None
    default_model: str
    suggestion_count: int
    selected_creators: Optional[List[int]] = None

class UserPreferenceUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    default_model: Optional[str] = None
    suggestion_count: Optional[int] = Field(default=None, ge=1, le=10)
    selected_creators: Optional[List[int]] = None

class PasswordReset(BaseModel):
    new_password: str = Field(min_length=6, description="Password must be at least 6 characters")

class UsersResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int

# USER CRUD ENDPOINTS
@router.get("/", response_model=UsersResponse)
async def list_users(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search by email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
):
    """List all users with pagination and filtering (Admin only)"""
    
    # Base query
    query = select(User)
    
    # Add search filter
    if search:
        query = query.where(User.email.ilike(f"%{search}%"))
    
    # Add status filters
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    if is_admin is not None:
        query = query.where(User.is_admin == is_admin)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0
    
    # Get paginated results
    paginated_query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(paginated_query)
    users = result.scalars().all()
    
    # Calculate pagination info
    pages = max(1, (total + limit - 1) // limit)
    current_page = (skip // limit) + 1
    
    # Convert to response models
    user_responses = [
        UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]
    
    return UsersResponse(
        items=user_responses,
        total=total,
        page=current_page,
        size=limit,
        pages=pages
    )

@router.get("/{user_id}", response_model=UserWithPreferencesResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Get user details by ID (Admin only)"""
    
    # Get user
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get user preferences
    prefs_query = select(UserPreference).where(UserPreference.user_id == user_id)
    prefs_result = await session.execute(prefs_query)
    preferences = prefs_result.scalar_one_or_none()
    
    # Build response
    user_response = UserWithPreferencesResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at,
        preferences=UserPreferenceResponse(
            id=preferences.id,
            user_id=preferences.user_id,
            openai_api_key=preferences.openai_api_key,
            default_model=preferences.default_model,
            suggestion_count=preferences.suggestion_count,
            selected_creators=preferences.selected_creators
        ) if preferences else None
    )
    
    return user_response

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new user (Admin only)"""
    
    # Check if user already exists
    existing_query = select(User).where(User.email == user_data.email)
    existing_result = await session.execute(existing_query)
    existing_user = existing_result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=user_data.is_active,
        is_admin=user_data.is_admin,
        is_verified=False  # User needs to verify email
    )
    
    session.add(new_user)
    await session.flush()  # Get the user ID
    
    # Create user preferences
    user_preferences = UserPreference(
        user_id=new_user.id,
        openai_api_key=user_data.openai_api_key,
        default_model=user_data.default_model,
        suggestion_count=user_data.suggestion_count,
        selected_creators=None
    )
    
    session.add(user_preferences)
    await session.commit()
    await session.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        is_admin=new_user.is_admin,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Update user information (Admin only)"""
    
    # Get user
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Prevent admin from demoting themselves
    if user_id == current_user.id and user_update.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own admin privileges"
        )
    
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Update the updated_at timestamp
    user.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete a user (Admin only)"""
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    # Get user
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Delete user (preferences will cascade delete if set up properly)
    await session.delete(user)
    await session.commit()
    
    return None

# USER STATUS MANAGEMENT
@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Activate a user (Admin only)"""
    
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user.is_active = True
    user.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Deactivate a user (Admin only)"""
    
    # Prevent admin from deactivating themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )
    
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/{user_id}/make-admin", response_model=UserResponse)
async def make_admin(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Grant admin privileges to a user (Admin only)"""
    
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user.is_admin = True
    user.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/{user_id}/remove-admin", response_model=UserResponse)
async def remove_admin(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Remove admin privileges from a user (Admin only)"""
    
    # Prevent admin from removing their own privileges
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own admin privileges"
        )
    
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user.is_admin = False
    user.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# PASSWORD MANAGEMENT
@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
async def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Reset a user's password (Admin only)"""
    
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    user.updated_at = datetime.utcnow()
    
    await session.commit()
    
    return {"message": "Password reset successfully"}

# USER PREFERENCES MANAGEMENT
@router.get("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Get user preferences (Admin only)"""
    
    # Check if user exists
    user_query = select(User).where(User.id == user_id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get preferences
    prefs_query = select(UserPreference).where(UserPreference.user_id == user_id)
    prefs_result = await session.execute(prefs_query)
    preferences = prefs_result.scalar_one_or_none()
    
    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreference(
            user_id=user_id,
            default_model="gpt-4",
            suggestion_count=3
        )
        session.add(preferences)
        await session.commit()
        await session.refresh(preferences)
    
    return UserPreferenceResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        openai_api_key=preferences.openai_api_key,
        default_model=preferences.default_model,
        suggestion_count=preferences.suggestion_count,
        selected_creators=preferences.selected_creators
    )

@router.patch("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    user_id: int,
    preferences_update: UserPreferenceUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Update user preferences (Admin only)"""
    
    # Check if user exists
    user_query = select(User).where(User.id == user_id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get or create preferences
    prefs_query = select(UserPreference).where(UserPreference.user_id == user_id)
    prefs_result = await session.execute(prefs_query)
    preferences = prefs_result.scalar_one_or_none()
    
    if not preferences:
        preferences = UserPreference(user_id=user_id)
        session.add(preferences)
    
    # Update preferences
    update_data = preferences_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    await session.commit()
    await session.refresh(preferences)
    
    return UserPreferenceResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        openai_api_key=preferences.openai_api_key,
        default_model=preferences.default_model,
        suggestion_count=preferences.suggestion_count,
        selected_creators=preferences.selected_creators
    )

# STATISTICS AND BULK OPERATIONS
@router.get("/stats/summary")
async def get_user_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Get user statistics summary (Admin only)"""
    
    # Total users
    total_query = select(func.count(User.id))
    total_result = await session.execute(total_query)
    total_users = total_result.scalar() or 0
    
    # Active users
    active_query = select(func.count(User.id)).where(User.is_active == True)
    active_result = await session.execute(active_query)
    active_users = active_result.scalar() or 0
    
    # Admin users
    admin_query = select(func.count(User.id)).where(User.is_admin == True)
    admin_result = await session.execute(admin_query)
    admin_users = admin_result.scalar() or 0
    
    # Verified users
    verified_query = select(func.count(User.id)).where(User.is_verified == True)
    verified_result = await session.execute(verified_query)
    verified_users = verified_result.scalar() or 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "admin_users": admin_users,
        "verified_users": verified_users,
        "unverified_users": total_users - verified_users,
    }

@router.post("/bulk-activate")
async def bulk_activate_users(
    user_ids: List[int] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Bulk activate users (Admin only)"""
    
    # Get users
    query = select(User).where(User.id.in_(user_ids))
    result = await session.execute(query)
    users = result.scalars().all()
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found with the provided IDs"
        )
    
    # Activate users
    updated_count = 0
    for user in users:
        if not user.is_active:
            user.is_active = True
            user.updated_at = datetime.utcnow()
            updated_count += 1
    
    await session.commit()
    
    return {
        "message": f"Successfully activated {updated_count} users",
        "total_processed": len(users),
        "updated_count": updated_count
    }

@router.post("/bulk-deactivate")
async def bulk_deactivate_users(
    user_ids: List[int] = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
):
    """Bulk deactivate users (Admin only)"""
    
    # Remove current user from the list to prevent self-deactivation
    user_ids = [uid for uid in user_ids if uid != current_user.id]
    
    if not user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid user IDs provided (cannot deactivate yourself)"
        )
    
    # Get users
    query = select(User).where(User.id.in_(user_ids))
    result = await session.execute(query)
    users = result.scalars().all()
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found with the provided IDs"
        )
    
    # Deactivate users
    updated_count = 0
    for user in users:
        if user.is_active:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            updated_count += 1
    
    await session.commit()
    
    return {
        "message": f"Successfully deactivated {updated_count} users",
        "total_processed": len(users),
        "updated_count": updated_count
    }