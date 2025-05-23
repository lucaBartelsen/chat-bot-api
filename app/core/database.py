# app/core/database.py - Fixed async database configuration

import os
from typing import AsyncGenerator
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for migrations and admin tasks
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Sync session factory for migrations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session():
    """Get synchronous database session for migrations"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def create_db_and_tables():
    """Create database tables"""
    try:
        async with engine.begin() as conn:
            # Create pgvector extension if it doesn't exist
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Create all tables
            await conn.run_sync(SQLModel.metadata.create_all)
            
        print("✅  Database tables created/verified")
        print("✅  pgvector extension enabled")
    except Exception as e:
        print(f"❌  Database initialization failed: {e}")
        raise


async def drop_db_and_tables():
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# Database health check
async def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        async with AsyncSessionLocal() as session:
            # Test basic connectivity
            await session.execute(text("SELECT 1"))
            
            # Test pgvector extension
            result = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            vector_installed = result.scalar() is not None
            
            if not vector_installed:
                print("⚠️  pgvector extension not installed")
                return False
                
            print("✅  Database health check passed")
            print("✅  pgvector extension confirmed")
            return True
            
    except Exception as e:
        print(f"❌  Database health check failed: {e}")
        return False