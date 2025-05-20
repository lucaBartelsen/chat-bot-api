import time
from typing import List, Optional, Tuple
import numpy as np
from sqlalchemy import select, func
from sqlmodel import Session
from pgvector.sqlalchemy import Vector, cosine_distance

from app.models.creator import VectorStore, Creator
from app.core.database import get_session

class VectorService:
    """Service for vector storage and similarity search"""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def store_conversation(
        self, 
        creator_id: int, 
        fan_message: str, 
        creator_response: str, 
        embedding: List[float]
    ) -> VectorStore:
        """Store a conversation with vector embedding"""
        
        # Create vector store entry
        vector_entry = VectorStore(
            creator_id=creator_id,
            fan_message=fan_message,
            creator_response=creator_response,
            embedding=embedding
        )
        
        # Add to database
        self.session.add(vector_entry)
        await self.session.commit()
        await self.session.refresh(vector_entry)
        
        return vector_entry
    
    async def find_similar_conversations(
        self, 
        creator_id: int, 
        embedding: List[float], 
        similarity_threshold: float = 0.7, 
        limit: int = 5
    ) -> List[Tuple[VectorStore, float]]:
        """Find similar conversations based on vector similarity"""
        
        # Query for similar conversations
        query = (
            select(VectorStore)
            .where(VectorStore.creator_id == creator_id)
            .order_by(cosine_distance(VectorStore.embedding, embedding))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        conversations = result.scalars().all()
        
        # Calculate similarity scores (1 - cosine distance)
        similar_conversations = []
        for conv in conversations:
            # Calculate cosine similarity (1 - cosine distance)
            similarity = 1 - cosine_distance(np.array(conv.embedding), np.array(embedding))
            
            # Only include if above threshold
            if similarity >= similarity_threshold:
                similar_conversations.append((conv, float(similarity)))
        
        return similar_conversations
    
    async def get_statistics(self) -> dict:
        """Get statistics about stored conversations"""
        
        # Count total vectors
        total_query = select(func.count(VectorStore.id))
        total_result = await self.session.execute(total_query)
        total_count = total_result.scalar()
        
        # Count vectors by creator
        creator_query = (
            select(Creator.name, func.count(VectorStore.id))
            .join(VectorStore, Creator.id == VectorStore.creator_id)
            .group_by(Creator.name)
        )
        creator_result = await self.session.execute(creator_query)
        creator_counts = {name: count for name, count in creator_result.all()}
        
        return {
            "total_vectors": total_count,
            "creators": creator_counts,
            "timestamp": time.time()
        }
    
    async def clear_vectors(self, creator_id: Optional[int] = None) -> int:
        """Clear stored vectors, optionally for a specific creator"""
        
        if creator_id:
            # Delete vectors for specific creator
            query = select(VectorStore).where(VectorStore.creator_id == creator_id)
        else:
            # Delete all vectors
            query = select(VectorStore)
        
        result = await self.session.execute(query)
        vectors = result.scalars().all()
        
        deleted_count = len(vectors)
        for vector in vectors:
            await self.session.delete(vector)
        
        await self.session.commit()
        
        return deleted_count