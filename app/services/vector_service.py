# File: app/services/vector_service.py
# Path: fanfix-api/app/services/vector_service.py

from typing import List, Dict, Any, Optional
import asyncpg
import os
import uuid

from app.core.config import settings

class VectorService:
    def __init__(self):
        self.pool = None
        self.connection_string = settings.DATABASE_URL
    
    async def init_pool(self):
        """Initialize connection pool if not already initialized"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.connection_string)
    
    async def find_similar_conversations(
        self, 
        embedding: List[float], 
        creator_id: str, 
        limit: int = 3, 
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find similar conversations using vector similarity"""
        await self.init_pool()
        
        query = """
        SELECT id, "fanMessage", "creatorResponses", 
               1 - (embedding <=> $1) as similarity
        FROM "VectorStore"
        WHERE "creatorId" = $2
          AND (1 - (embedding <=> $1)) > $3
        ORDER BY similarity DESC
        LIMIT $4
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, embedding, creator_id, similarity_threshold, limit)
                
                result = []
                for row in rows:
                    result.append({
                        "id": row["id"],
                        "fanMessage": row["fanMessage"],
                        "creatorResponses": row["creatorResponses"],
                        "similarity": row["similarity"]
                    })
                
                return result
            except Exception as e:
                print(f"Error finding similar conversations: {e}")
                # If the query fails, return an empty list
                return []
    
    async def store_conversation(
        self, 
        creator_id: str, 
        fan_message: str, 
        creator_responses: List[str], 
        embedding: List[float]
    ) -> str:
        """Store a conversation with its embedding vector"""
        await self.init_pool()
        
        query = """
        INSERT INTO "VectorStore" ("id", "creatorId", "fanMessage", "creatorResponses", embedding)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        
        conversation_id = str(uuid.uuid4())
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    query, 
                    conversation_id,
                    creator_id, 
                    fan_message, 
                    creator_responses, 
                    embedding
                )
                return row["id"]
            except Exception as e:
                print(f"Error storing conversation: {e}")
                # Return a generated ID even if storage fails
                return conversation_id
    
    async def get_conversation_stats(self, creator_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about stored conversations"""
        await self.init_pool()
        
        try:
            if creator_id:
                query = """
                SELECT 
                    COUNT(*) as total_count,
                    MAX(timestamp) as latest_timestamp
                FROM "VectorStore"
                WHERE "creatorId" = $1
                """
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow(query, creator_id)
            else:
                query = """
                SELECT 
                    COUNT(*) as total_count,
                    MAX(timestamp) as latest_timestamp
                FROM "VectorStore"
                """
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow(query)
                    
            return {
                "total_conversations": row["total_count"] if row["total_count"] else 0,
                "latest_timestamp": row["latest_timestamp"]
            }
        except Exception as e:
            print(f"Error getting conversation stats: {e}")
            return {
                "total_conversations": 0,
                "latest_timestamp": None
            }
    
    async def clear_conversations(self, creator_id: Optional[str] = None) -> int:
        """Clear stored conversations, optionally by creator ID"""
        await self.init_pool()
        
        try:
            if creator_id:
                query = 'DELETE FROM "VectorStore" WHERE "creatorId" = $1'
                async with self.pool.acquire() as conn:
                    result = await conn.execute(query, creator_id)
            else:
                query = 'DELETE FROM "VectorStore"'
                async with self.pool.acquire() as conn:
                    result = await conn.execute(query)
                    
            # Parse the DELETE count from the result string
            # Example format: "DELETE 42"
            count = int(result.split()[1]) if "DELETE" in result else 0
            return count
        except Exception as e:
            print(f"Error clearing conversations: {e}")
            return 0