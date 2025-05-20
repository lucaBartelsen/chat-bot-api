# File: app/auth/db.py (updated)
# Path: fanfix-api/app/auth/db.py

from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union, cast
import uuid
from fastapi_users.db.base import BaseUserDatabase
from prisma import Prisma
from pydantic import EmailStr
from app.auth.models import UserCreate, UserDB, UserUpdate

ID = TypeVar("ID", bound=Any)
UP = TypeVar("UP", bound=Union[Dict[str, Any], UserDB])

class PrismaUserDatabase(BaseUserDatabase[UP, ID]):
    """
    Database adapter for FastAPI Users using Prisma ORM.
    """

    prisma_client: Prisma
    user_table_name: str

    def __init__(self, prisma_client: Prisma, user_table_name: str = "User"):
        self.prisma_client = prisma_client
        self.user_table_name = user_table_name

    async def get(self, id: ID) -> Optional[UP]:
        """Get a user by ID."""
        try:
            user = await self.prisma_client.user.find_unique(
                where={"id": str(id)},
            )
            if user:
                return self._model_to_dict(user)
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    async def get_by_email(self, email: str) -> Optional[UP]:
        """Get a user by email."""
        try:
            user = await self.prisma_client.user.find_unique(
                where={"email": email},
            )
            if user:
                return self._model_to_dict(user)
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    async def create(self, create_dict: Dict[str, Any]) -> UP:
        """Create a user."""
        try:
            user_data = {
                "email": create_dict["email"],
                "hashed_password": create_dict["hashed_password"],
                "is_active": create_dict.get("is_active", True),
                "is_superuser": create_dict.get("is_superuser", False),
                "is_verified": create_dict.get("is_verified", False),
            }

            # Allow explicit ID if provided
            if "id" in create_dict:
                user_data["id"] = str(create_dict["id"])

            user = await self.prisma_client.user.create(data=user_data)
            return self._model_to_dict(user)
        except Exception as e:
            print(f"Error creating user: {e}")
            raise

    async def update(self, user_id: ID, update_dict: Dict[str, Any]) -> UP:
        """Update a user."""
        try:
            update_data = {}
            
            # Only include fields that are provided
            if "email" in update_dict:
                update_data["email"] = update_dict["email"]
            if "hashed_password" in update_dict:
                update_data["hashed_password"] = update_dict["hashed_password"]
            if "is_active" in update_dict:
                update_data["is_active"] = update_dict["is_active"]
            if "is_superuser" in update_dict:
                update_data["is_superuser"] = update_dict["is_superuser"]
            if "is_verified" in update_dict:
                update_data["is_verified"] = update_dict["is_verified"]

            user = await self.prisma_client.user.update(
                where={"id": str(user_id)},
                data=update_data,
            )
            return self._model_to_dict(user)
        except Exception as e:
            print(f"Error updating user: {e}")
            raise

    async def delete(self, user_id: ID) -> None:
        """Delete a user."""
        try:
            await self.prisma_client.user.delete(
                where={"id": str(user_id)},
            )
        except Exception as e:
            print(f"Error deleting user: {e}")
            raise
    
    def _model_to_dict(self, model) -> UP:
        """Convert a Prisma model to a dictionary."""
        if hasattr(model, "dict"):
            return cast(UP, model.dict())
        elif hasattr(model, "__dict__"):
            return cast(UP, model.__dict__)
        else:
            # Fallback to a simple dictionary conversion
            result = {}
            for key in dir(model):
                if not key.startswith("_") and key != "model_fields_set":
                    result[key] = getattr(model, key)
            return cast(UP, result)