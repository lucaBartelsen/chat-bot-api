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
                
            # Check if VectorStore table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'VectorStore')"
            )
            
            # Check if vector index exists
            if table_exists:
                index_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname = 'vectorstore_embedding_idx')"
                )
                
                if not index_exists:
                    # Create the vector index manually
                    print("Creating vector index for VectorStore table...")
                    try:
                        # Create the vector index using raw SQL
                        await conn.execute(
                            "CREATE INDEX vectorstore_embedding_idx ON \"VectorStore\" USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
                        )
                        print("Vector index created successfully")
                    except Exception as e:
                        print(f"Error creating vector index: {e}")
                        # Continue execution even if index creation fails
                        # This allows the application to start and the index can be created later
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
    
    return pool

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