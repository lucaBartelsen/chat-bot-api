# File: app/auth/users.py (updated)
# Path: fanfix-api/app/auth/users.py

from typing import Optional, Union, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, Request
from fastapi_users import FastAPIUsers
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
# Import your custom PrismaUserDatabase from local db.py instead of fastapi_users
from app.auth.db import PrismaUserDatabase
import uuid

from prisma import Prisma
from app.core.config import settings
from app.auth.models import User, UserCreate, UserDB, UserUpdate

# Prisma client management
@asynccontextmanager
async def get_prisma_client() -> AsyncGenerator[Prisma, None]:
    client = Prisma()
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()

# Get user DB from Prisma client - using your custom PrismaUserDatabase
async def get_user_db(prisma_client: Prisma = Depends(get_prisma_client)):
    yield PrismaUserDatabase(prisma_client, user_table_name="User")

# User manager to handle user operations
class UserManager(UUIDIDMixin, BaseUserManager[UserCreate, UserDB]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
        
        # Create default user preferences
        async with get_prisma_client() as prisma:
            try:
                await prisma.userpreferences.create(
                    data={
                        "userId": str(user.id),
                        "numSuggestions": 3,
                        "modelName": settings.DEFAULT_MODEL
                    }
                )
            except Exception as e:
                print(f"Error creating user preferences: {e}")

    async def on_after_forgot_password(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgotten their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

    async def on_after_update(
        self, user: UserDB, update_dict: dict, request: Optional[Request] = None
    ):
        print(f"User {user.id} has been updated with {update_dict}.")
        
    async def on_before_delete(
        self, user: UserDB, request: Optional[Request] = None
    ):
        print(f"User {user.id} is about to be deleted.")
        
        # Delete user preferences
        try:
            async with get_prisma_client() as prisma:
                await prisma.userpreferences.delete(
                    where={"userId": str(user.id)}
                )
        except Exception as e:
            print(f"Error deleting user preferences: {e}")

# Get user manager
async def get_user_manager(user_db = Depends(get_user_db)):
    yield UserManager(user_db)

# Configure JWT authentication
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.JWT_SECRET, 
        lifetime_seconds=settings.JWT_EXPIRES_MINUTES * 60,
        token_url="auth/jwt/login"
    )

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers(
    get_user_manager,
    [auth_backend],
)

# Dependencies for current user
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

# Dependency to get Prisma client
async def get_prisma():
    async with get_prisma_client() as prisma:
        yield prisma

async def create_admin_user(email: str, password: str):
    """
    Create a new admin user with superuser privileges.
    This function is called from the Makefile.
    
    Args:
        email: The email address for the admin user
        password: The password for the admin user
    """
    try:
        async with get_prisma_client() as prisma:
            # Check if user already exists
            existing_user = await prisma.user.find_unique(
                where={"email": email}
            )
            
            if existing_user:
                print(f"User with email {email} already exists.")
                
                # If the user exists but is not a superuser, make them a superuser
                if not existing_user.is_superuser:
                    await prisma.user.update(
                        where={"id": existing_user.id},
                        data={"is_superuser": True, "is_active": True, "is_verified": True}
                    )
                    print(f"User {email} has been granted admin privileges.")
                else:
                    print(f"User {email} is already an admin.")
                
                return
            
            # Create a new user with admin privileges
            # Hash the password
            from app.core.security import get_password_hash
            hashed_password = get_password_hash(password)
            
            # Create the user
            user = await prisma.user.create(
                data={
                    "email": email,
                    "hashed_password": hashed_password,
                    "is_superuser": True,
                    "is_active": True,
                    "is_verified": True
                }
            )
            
            # Create default user preferences
            await prisma.userpreferences.create(
                data={
                    "userId": user.id,
                    "numSuggestions": 3,
                    "modelName": "gpt-3.5-turbo"
                }
            )
            
            print(f"Admin user {email} created successfully!")
    
    except Exception as e:
        print(f"Error creating admin user: {e}")
        raise