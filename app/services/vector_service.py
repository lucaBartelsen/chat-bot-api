import time
from typing import Any, List, Optional, Tuple, Union, Dict
import numpy as np
from sqlalchemy import select, func, delete
from sqlmodel import Session
from pgvector.sqlalchemy import Vector

from app.models.creator import (
    VectorStore, 
    Creator, 
    StyleExample, 
    ResponseExample,
    CreatorResponse
)
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
    
    async def store_style_example(
        self,
        creator_id: int,
        fan_message: str,
        creator_response: str,
        category: Optional[str] = None,
        embedding: Optional[List[float]] = None
    ) -> StyleExample:
        """Store a style example with vector embedding"""
        
        # Create style example entry
        example = StyleExample(
            creator_id=creator_id,
            fan_message=fan_message,
            creator_response=creator_response,
            category=category,
            embedding=embedding
        )
        
        # Add to database
        self.session.add(example)
        await self.session.commit()
        await self.session.refresh(example)
        
        return example
    
    async def store_response_example(
        self,
        creator_id: int,
        fan_message: str,
        responses: List[str],
        rankings: Optional[List[int]] = None,
        category: Optional[str] = None,
        embedding: Optional[List[float]] = None
    ) -> ResponseExample:
        """Store a response example with multiple creator responses and embedding"""
        
        # Create response example entry
        example = ResponseExample(
            creator_id=creator_id,
            fan_message=fan_message,
            category=category,
            embedding=embedding
        )
        
        # Add to database
        self.session.add(example)
        await self.session.commit()
        await self.session.refresh(example)
        
        # Add individual responses
        for i, response_text in enumerate(responses):
            # Get ranking if available, otherwise default to position
            ranking = rankings[i] if rankings and i < len(rankings) else i + 1
            
            # Create creator response
            creator_response = CreatorResponse(
                example_id=example.id,
                response_text=response_text,
                ranking=ranking
            )
            
            # Add to database
            self.session.add(creator_response)
        
        # Commit all responses
        await self.session.commit()
        await self.session.refresh(example)
        
        return example
    
    async def find_similar_conversations(
        self, 
        creator_id: int, 
        embedding: List[float], 
        similarity_threshold: float = 0.7, 
        limit: int = 5
    ) -> List[Tuple[VectorStore, float]]:
        """Find similar conversations based on vector similarity"""
        
        # Query for similar conversations using cosine distance
        query = (
            select(VectorStore)
            .where(VectorStore.creator_id == creator_id)
            .order_by(VectorStore.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        conversations = result.scalars().all()
        
        # Calculate similarity scores (1 - cosine distance)
        similar_conversations = []
        for conv in conversations:
            # Calculate cosine similarity using numpy
            similarity = self._calculate_similarity(conv.embedding, embedding)
            
            # Only include if above threshold
            if similarity >= similarity_threshold:
                similar_conversations.append((conv, float(similarity)))
        
        return similar_conversations
    
    async def find_similar_style_examples(
        self,
        creator_id: int,
        embedding: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Tuple[StyleExample, float]]:
        """Find similar style examples based on vector similarity"""
        
        # Base query
        query = (
            select(StyleExample)
            .where(StyleExample.creator_id == creator_id)
        )
        
        # Add category filter if provided
        if category:
            query = query.where(StyleExample.category == category)
        
        # Order by cosine similarity and limit results
        query = (
            query
            .order_by(StyleExample.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        examples = result.scalars().all()
        
        # Calculate similarity scores
        similar_examples = []
        for example in examples:
            # Calculate cosine similarity
            similarity = self._calculate_similarity(example.embedding, embedding)
            
            # Only include if above threshold
            if similarity >= similarity_threshold:
                similar_examples.append((example, float(similarity)))
        
        return similar_examples
    
    async def find_similar_response_examples(
        self,
        creator_id: int,
        embedding: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Tuple[ResponseExample, float]]:
        """Find similar response examples based on vector similarity"""
        
        # Base query
        query = (
            select(ResponseExample)
            .where(ResponseExample.creator_id == creator_id)
        )
        
        # Add category filter if provided
        if category:
            query = query.where(ResponseExample.category == category)
        
        # Order by cosine similarity and limit results
        query = (
            query
            .order_by(ResponseExample.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        examples = result.scalars().all()
        
        # Calculate similarity scores
        similar_examples = []
        for example in examples:
            # Calculate cosine similarity
            similarity = self._calculate_similarity(example.embedding, embedding)
            
            # Only include if above threshold
            if similarity >= similarity_threshold:
                similar_examples.append((example, float(similarity)))
        
        return similar_examples
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        # Convert to numpy arrays
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # Normalize the vectors
        v1_norm = v1 / np.linalg.norm(v1)
        v2_norm = v2 / np.linalg.norm(v2)
        
        # Calculate cosine similarity
        return float(np.dot(v1_norm, v2_norm))
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored conversations and examples"""
        
        # Count total vectors by type
        vector_count_query = select(func.count(VectorStore.id))
        vector_count_result = await self.session.execute(vector_count_query)
        vector_count = vector_count_result.scalar()
        
        style_count_query = select(func.count(StyleExample.id))
        style_count_result = await self.session.execute(style_count_query)
        style_count = style_count_result.scalar()
        
        response_count_query = select(func.count(ResponseExample.id))
        response_count_result = await self.session.execute(response_count_query)
        response_count = response_count_result.scalar()
        
        # Count vectors by creator
        creator_query = (
            select(Creator.name, func.count(VectorStore.id))
            .join(VectorStore, Creator.id == VectorStore.creator_id)
            .group_by(Creator.name)
        )
        creator_result = await self.session.execute(creator_query)
        creator_counts = {name: count for name, count in creator_result.all()}
        
        # Count style examples by creator
        style_creator_query = (
            select(Creator.name, func.count(StyleExample.id))
            .join(StyleExample, Creator.id == StyleExample.creator_id)
            .group_by(Creator.name)
        )
        style_creator_result = await self.session.execute(style_creator_query)
        style_creator_counts = {name: count for name, count in style_creator_result.all()}
        
        # Count response examples by creator
        response_creator_query = (
            select(Creator.name, func.count(ResponseExample.id))
            .join(ResponseExample, Creator.id == ResponseExample.creator_id)
            .group_by(Creator.name)
        )
        response_creator_result = await self.session.execute(response_creator_query)
        response_creator_counts = {name: count for name, count in response_creator_result.all()}
        
        return {
            "total_vectors": vector_count,
            "total_style_examples": style_count,
            "total_response_examples": response_count,
            "creators_vectors": creator_counts,
            "creators_style_examples": style_creator_counts,
            "creators_response_examples": response_creator_counts,
            "timestamp": time.time()
        }
    
    async def clear_vectors(self, creator_id: Optional[int] = None) -> Dict[str, int]:
        """Clear stored vectors, optionally for a specific creator"""
        
        # Initialize counters
        deleted_counts = {
            "vector_store": 0,
            "style_examples": 0,
            "response_examples": 0
        }
        
        # Delete from vector store
        if creator_id:
            vector_query = select(VectorStore).where(VectorStore.creator_id == creator_id)
        else:
            vector_query = select(VectorStore)
        
        vector_result = await self.session.execute(vector_query)
        vectors = vector_result.scalars().all()
        
        deleted_counts["vector_store"] = len(vectors)
        for vector in vectors:
            await self.session.delete(vector)
        
        # Delete style examples
        if creator_id:
            style_query = select(StyleExample).where(StyleExample.creator_id == creator_id)
        else:
            style_query = select(StyleExample)
        
        style_result = await self.session.execute(style_query)
        styles = style_result.scalars().all()
        
        deleted_counts["style_examples"] = len(styles)
        for style in styles:
            await self.session.delete(style)
        
        # Delete response examples (responses will cascade)
        if creator_id:
            response_query = select(ResponseExample).where(ResponseExample.creator_id == creator_id)
        else:
            response_query = select(ResponseExample)
        
        response_result = await self.session.execute(response_query)
        responses = response_result.scalars().all()
        
        deleted_counts["response_examples"] = len(responses)
        for response in responses:
            await self.session.delete(response)
        
        # Commit all deletions
        await self.session.commit()
        
        return deleted_counts