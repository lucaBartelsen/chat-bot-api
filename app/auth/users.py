# File: app/auth/users.py (updated)
# Path: fanfix-api/app/auth/users.py

from typing import Optional, Union, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import PrismaUserDatabase
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

# User database adapter to work with Prisma
class PrismaUserDatabaseAdapter(PrismaUserDatabase):
    """Custom adapter for FastAPI Users to work with Prisma ORM"""
    
    async def get(self, id: uuid.UUID) -> Optional[UserDB]:
        user = await self.prisma_client.user.find_unique(
            where={"id": str(id)},
        )
        if user:
            return UserDB(**user.dict())
        return None

    async def get_by_email(self, email: str) -> Optional[UserDB]:
        user = await self.prisma_client.user.find_unique(
            where={"email": email},
        )
        if user:
            return UserDB(**user.dict())
        return None

    async def create(self, user: UserDB) -> UserDB:
        created_user = await self.prisma_client.user.create(
            data={
                "id": str(user.id),
                "email": user.email,
                "hashed_password": user.hashed_password,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
            }
        )
        return UserDB(**created_user.dict())

    async def update(self, user: UserDB) -> UserDB:
        updated_user = await self.prisma_client.user.update(
            where={"id": str(user.id)},
            data={
                "email": user.email,
                "hashed_password": user.hashed_password,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
            }
        )
        return UserDB(**updated_user.dict())

    async def delete(self, user: UserDB) -> None:
        await self.prisma_client.user.delete(
            where={"id": str(user.id)},
        )

# Get user DB from Prisma client
async def get_user_db(prisma_client: Prisma = Depends(get_prisma_client)):
    yield PrismaUserDatabaseAdapter(prisma_client)

# User manager to handle user operations
class UserManager(UUIDIDMixin, BaseUserManager[UserCreate, UserDB]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
        
        # Create default user preferences
        async with get_prisma_client() as prisma:
            await prisma.userpreferences.create(
                data={
                    "userId": str(user.id),
                    "numSuggestions": 3,
                    "modelName": settings.DEFAULT_MODEL
                }
            )

    async def on_after_forgot_password(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

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
async def get_user_manager(user_db: PrismaUserDatabaseAdapter = Depends(get_user_db)):
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
fastapi_users = FastAPIUsers[User, uuid.UUID](
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