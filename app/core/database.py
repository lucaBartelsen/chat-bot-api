import os
from typing import Any, AsyncGenerator, List, Optional

from sqlmodel import Field, Relationship, SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, text
from pgvector.sqlalchemy import Vector

# Database URL from environment variable or default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fanfix")
SYNC_DATABASE_URL = os.environ.get("SYNC_DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/fanfix")

# Async engine for normal operations
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine for initialization and some operations
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False, future=True)

# Database session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session.
    Returns an async generator that yields a SQLAlchemy AsyncSession.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Function to initialize pgvector extension
def init_db():
    with Session(sync_engine) as session:
        # Create pgvector extension if it doesn't exist
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()
        
    # Create all tables
    SQLModel.metadata.create_all(sync_engine)