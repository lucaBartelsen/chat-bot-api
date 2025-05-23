# app/api/auth.py - Fixed to use AsyncSession consistently

from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import ValidationError

from app.models.user import User, UserPreference
from app.core.database import get_session
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.auth.users import get_current_active_user

router = APIRouter()

@router.post("/login", summary="OAuth2 compatible token login")
async def login_access_token(
    session: AsyncSession = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> dict:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    This endpoint follows the OAuth2 password flow standard.
    
    - **username**: Email address of the user (required)
    - **password**: Password of the user (required)
    - **client_id**: Not required, can be left empty
    - **client_secret**: Not required, can be left empty
    - **scope**: Not required, can be left empty
    """
    # Find user by email
    query = select(User).where(User.email == form_data.username)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    email: str = Body(...),
    password: str = Body(...),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Register a new user
    """
    # Check if user already exists
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        is_active=True,
        is_verified=False  # User needs to verify email
    )
    
    # Create user preferences
    user_preferences = UserPreference(user=user)
    
    # Add user and preferences to database
    session.add(user)
    session.add(user_preferences)
    await session.commit()
    await session.refresh(user)
    
    return user

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user
    """
    return current_user

@router.get("/preferences", response_model=UserPreference)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
) -> UserPreference:
    """
    Get user preferences
    """
    query = select(UserPreference).where(UserPreference.user_id == current_user.id)
    result = await session.execute(query)
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Create preferences if they don't exist
        preferences = UserPreference(user_id=current_user.id)
        session.add(preferences)
        await session.commit()
        await session.refresh(preferences)
    
    return preferences

@router.patch("/preferences", response_model=UserPreference)
async def update_user_preferences(
    preferences_update: UserPreference,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
) -> UserPreference:
    """
    Update user preferences
    """
    query = select(UserPreference).where(UserPreference.user_id == current_user.id)
    result = await session.execute(query)
    db_preferences = result.scalar_one_or_none()
    
    if not db_preferences:
        # Create preferences if they don't exist
        preferences_update.user_id = current_user.id
        session.add(preferences_update)
        await session.commit()
        await session.refresh(preferences_update)
        return preferences_update
    
    # Update preferences
    # Updated for Pydantic v2: dict() -> model_dump()
    for key, value in preferences_update.model_dump(exclude_unset=True).items():
        if key != "user_id":  # Prevent changing user_id
            setattr(db_preferences, key, value)
    
    await session.commit()
    await session.refresh(db_preferences)
    
    return db_preferences