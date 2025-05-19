# File: app/auth/db.py
# Path: fanfix-api/app/auth/db.py

from typing import Optional, Dict, Any, Type, Generic, TypeVar
import uuid
from pydantic import EmailStr
from fastapi_users.db import BaseUserDatabase
from prisma import Prisma

# Type variables
ID = TypeVar("ID")
UP = TypeVar("UP", bound=Dict[str, Any])

class PrismaUserDatabase(Generic[UP, ID]):
    """
    Database adapter for FastAPI Users using Prisma ORM.
    """

    prisma_client: Prisma
    user_table_name: str = "User"

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

    async def create(self, user_dict: Dict[str, Any]) -> UP:
        """Create a user."""
        try:
            user_data = {
                "email": user_dict["email"],
                "hashed_password": user_dict["hashed_password"],
                "is_active": user_dict.get("is_active", True),
                "is_superuser": user_dict.get("is_superuser", False),
                "is_verified": user_dict.get("is_verified", False),
            }

            # Allow explicit ID if provided
            if "id" in user_dict:
                user_data["id"] = str(user_dict["id"])

            user = await self.prisma_client.user.create(data=user_data)
            return self._model_to_dict(user)
        except Exception as e:
            print(f"Error creating user: {e}")
            raise

    async def update(self, user_dict: Dict[str, Any]) -> UP:
        """Update a user."""
        try:
            if "id" not in user_dict:
                raise ValueError("User ID is required for update")
                
            update_data = {}
            
            # Only include fields that are provided
            if "email" in user_dict:
                update_data["email"] = user_dict["email"]
            if "hashed_password" in user_dict:
                update_data["hashed_password"] = user_dict["hashed_password"]
            if "is_active" in user_dict:
                update_data["is_active"] = user_dict["is_active"]
            if "is_superuser" in user_dict:
                update_data["is_superuser"] = user_dict["is_superuser"]
            if "is_verified" in user_dict:
                update_data["is_verified"] = user_dict["is_verified"]

            user = await self.prisma_client.user.update(
                where={"id": str(user_dict["id"])},
                data=update_data,
            )
            return self._model_to_dict(user)
        except Exception as e:
            print(f"Error updating user: {e}")
            raise

    async def delete(self, user: Dict[str, Any]) -> None:
        """Delete a user."""
        try:
            if "id" not in user:
                raise ValueError("User ID is required for deletion")
                
            await self.prisma_client.user.delete(
                where={"id": str(user["id"])},
            )
        except Exception as e:
            print(f"Error deleting user: {e}")
            raise
    
    def _model_to_dict(self, model) -> Dict[str, Any]:
        """Convert a Prisma model to a dictionary."""
        if hasattr(model, "dict"):
            return model.dict()
        elif hasattr(model, "__dict__"):
            return model.__dict__
        else:
            # Fallback to a simple dictionary conversion
            result = {}
            for key in dir(model):
                if not key.startswith("_") and key != "model_fields_set":
                    result[key] = getattr(model, key)
            return result