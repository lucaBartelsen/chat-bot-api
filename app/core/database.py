# File: app/core/database.py
# Path: fanfix-api/app/core/database.py

import asyncpg
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from app.core.config import settings

# Initialize the PostgreSQL connection pool
async def init_db_pool():
    """Initialize the PostgreSQL connection pool with pgvector extension"""
    pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=2,
        max_size=10
    )
    
    # Check if the pool is created successfully
    if not pool:
        raise Exception("Failed to create database connection pool")
    
    # Verify pgvector extension is enabled
    async with pool.acquire() as conn:
        try:
            # Check pgvector extension
            pgvector_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            
            if not pgvector_exists:
                # Try to create the extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                print("pgvector extension enabled successfully")
            else:
                print("pgvector extension is already enabled")
                
            # Create tables if they don't exist
            await create_tables(conn)
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
    
    return pool

async def create_tables(conn):
    """Create database tables if they don't exist"""
    # Create the User table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS "User" (
        "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "email" VARCHAR(255) UNIQUE NOT NULL,
        "hashed_password" VARCHAR(255) NOT NULL,
        "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
        "is_superuser" BOOLEAN NOT NULL DEFAULT FALSE,
        "is_verified" BOOLEAN NOT NULL DEFAULT FALSE,
        "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "last_login" TIMESTAMP
    )
    """)
    
    # Create the UserPreferences table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS "UserPreferences" (
        "userId" UUID PRIMARY KEY,
        "selectedCreatorId" UUID,
        "openaiApiKey" VARCHAR(255),
        "modelName" VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
        "numSuggestions" INTEGER DEFAULT 3,
        FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE
    )
    """)
    
    # Create the Creator table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS "Creator" (
        "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "name" VARCHAR(255) NOT NULL,
        "description" TEXT,
        "avatarUrl" VARCHAR(255),
        "active" BOOLEAN DEFAULT TRUE,
        "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create the CreatorStyle table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS "CreatorStyle" (
        "creatorId" UUID PRIMARY KEY,
        "approvedEmojis" TEXT[],
        "caseStyle" VARCHAR(50),
        "textReplacements" JSONB,
        "sentenceSeparators" TEXT[],
        "punctuationRules" JSONB,
        "abbreviations" JSONB,
        "messageLengthPreference" VARCHAR(50),
        "styleInstructions" TEXT,
        "toneRange" VARCHAR(50),
        FOREIGN KEY ("creatorId") REFERENCES "Creator" ("id") ON DELETE CASCADE
    )
    """)
    
    # Create the StyleExample table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS "StyleExample" (
        "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "creatorId" UUID NOT NULL,
        "fanMessage" TEXT NOT NULL,
        "creatorResponses" TEXT[] NOT NULL,
        "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY ("creatorId") REFERENCES "Creator" ("id") ON DELETE CASCADE
    )
    """)
    
    # Create the VectorStore table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS "VectorStore" (
        "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "creatorId" UUID NOT NULL,
        "fanMessage" TEXT NOT NULL,
        "creatorResponses" TEXT[] NOT NULL,
        "embedding" vector(1536),
        "similarityScore" FLOAT,
        "timestamp" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY ("creatorId") REFERENCES "Creator" ("id") ON DELETE CASCADE
    )
    """)
    
    # Create indexes
    await conn.execute("""
    CREATE INDEX IF NOT EXISTS "idx_creator_active" ON "Creator" ("active")
    """)
    
    await conn.execute("""
    CREATE INDEX IF NOT EXISTS "idx_vectorstore_creator" ON "VectorStore" ("creatorId")
    """)
    
    # Create an IVF index for vector similarity search if it doesn't exist
    # This uses the ivfflat index type which is optimal for larger datasets
    try:
        # Check if the index already exists
        index_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'idx_vectorstore_embedding'
        )
        """)
        
        if not index_exists:
            await conn.execute("""
            CREATE INDEX "idx_vectorstore_embedding" ON "VectorStore" 
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
            """)
            print("Created vector similarity search index")
    except Exception as e:
        print(f"Could not create vector index: {e}")
        # Continue anyway, as this is an optimization

# Context manager for database access
@asynccontextmanager
async def get_db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """Context manager for database pool access"""
    pool = await init_db_pool()
    try:
        yield pool
    finally:
        await pool.close()

# Function to get a database connection
async def get_db_conn():
    """Get a database connection from the pool"""
    pool = await init_db_pool()
    try:
        async with pool.acquire() as conn:
            yield conn
    finally:
        await pool.close()