# app/services/vector_service.py - Fixed async/await handling with proper conversation storage

from typing import List, Tuple, Optional, Any
import numpy as np
from sqlmodel import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.creator import StyleExample, ResponseExample, CreatorResponse, VectorStore


class VectorService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def store_style_example(
        self,
        creator_id: int,
        fan_message: str,
        creator_response: str,
        embedding: List[float],
        category: Optional[str] = None
    ) -> StyleExample:
        """Store a style example with vector embedding"""
        
        # Create StyleExample instance
        example = StyleExample(
            creator_id=creator_id,
            fan_message=fan_message,
            creator_response=creator_response,
            category=category,
            embedding=embedding  # Store as list, will be converted to numpy array by pgvector
        )
        
        # Add to session
        self.session.add(example)
        
        # Commit and refresh
        await self.session.commit()
        await self.session.refresh(example)
        
        return example

    async def store_response_example(
        self,
        creator_id: int,
        fan_message: str,
        responses: List[str],
        embedding: List[float],
        rankings: Optional[List[int]] = None,
        category: Optional[str] = None
    ) -> ResponseExample:
        """Store a response example with multiple responses and vector embedding"""
        
        # Create ResponseExample instance
        example = ResponseExample(
            creator_id=creator_id,
            fan_message=fan_message,
            category=category,
            embedding=embedding  # Store as list, will be converted to numpy array by pgvector
        )
        
        # Add to session
        self.session.add(example)
        
        # Flush to get the ID
        await self.session.flush()
        
        # Create individual responses
        for i, response_text in enumerate(responses):
            ranking = None
            if rankings and i < len(rankings):
                ranking = rankings[i]
            
            creator_response = CreatorResponse(
                example_id=example.id,
                response_text=response_text,
                ranking=ranking
            )
            self.session.add(creator_response)
        
        # Commit everything
        await self.session.commit()
        await self.session.refresh(example)
        
        return example

    async def store_vector_example(
        self,
        creator_id: int,
        fan_message: str,
        creator_response: str,
        embedding: List[float]
    ) -> VectorStore:
        """Store a conversation example in the vector store"""
        
        # Create VectorStore instance
        vector_item = VectorStore(
            creator_id=creator_id,
            fan_message=fan_message,
            creator_response=creator_response,
            embedding=embedding  # Store as list, will be converted to numpy array by pgvector
        )
        
        # Add to session
        self.session.add(vector_item)
        
        # Commit and refresh
        await self.session.commit()
        await self.session.refresh(vector_item)
        
        return vector_item

    async def store_conversation(
        self,
        creator_id: int,
        fan_message: str,
        creator_response: str,
        embedding: List[float]
    ) -> VectorStore:
        """Store a conversation example in the vector store"""
        
        # Create VectorStore instance
        vector_item = VectorStore(
            creator_id=creator_id,
            fan_message=fan_message,
            creator_response=creator_response,
            embedding=embedding  # Store as list, will be converted to numpy array by pgvector
        )
        
        # Add to session
        self.session.add(vector_item)
        
        # Commit and refresh
        await self.session.commit()
        await self.session.refresh(vector_item)
        
        return vector_item

    async def find_similar_style_examples(
        self,
        creator_id: int,
        embedding: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Tuple[StyleExample, float]]:
        """Find style examples similar to the given embedding using cosine similarity"""
        
        # Convert embedding to string format for SQL
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # Build query with similarity search
        query = select(
            StyleExample,
            # Calculate cosine similarity using pgvector
            (1 - func.cosine_distance(StyleExample.embedding, embedding_str)).label('similarity')
        ).where(
            StyleExample.creator_id == creator_id
        )
        
        # Add category filter if specified
        if category:
            query = query.where(StyleExample.category == category)
        
        # Filter by similarity threshold and order by similarity
        query = query.where(
            (1 - func.cosine_distance(StyleExample.embedding, embedding_str)) >= similarity_threshold
        ).order_by(
            func.cosine_distance(StyleExample.embedding, embedding_str)
        ).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        rows = result.all()
        
        # Return tuples of (example, similarity_score)
        return [(row[0], float(row[1])) for row in rows]

    async def find_similar_response_examples(
        self,
        creator_id: int,
        embedding: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Tuple[ResponseExample, float]]:
        """Find response examples similar to the given embedding using cosine similarity"""
        
        # Convert embedding to string format for SQL
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # Build query with similarity search
        query = select(
            ResponseExample,
            # Calculate cosine similarity using pgvector
            (1 - func.cosine_distance(ResponseExample.embedding, embedding_str)).label('similarity')
        ).where(
            ResponseExample.creator_id == creator_id
        )
        
        # Add category filter if specified
        if category:
            query = query.where(ResponseExample.category == category)
        
        # Filter by similarity threshold and order by similarity
        query = query.where(
            (1 - func.cosine_distance(ResponseExample.embedding, embedding_str)) >= similarity_threshold
        ).order_by(
            func.cosine_distance(ResponseExample.embedding, embedding_str)
        ).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        rows = result.all()
        
        # Return tuples of (example, similarity_score)
        return [(row[0], float(row[1])) for row in rows]

    async def find_similar_conversations(
        self,
        creator_id: int,
        embedding: List[float],
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[Tuple[VectorStore, float]]:
        """Find conversation examples similar to the given embedding"""
        
        # Convert embedding to string format for SQL
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # Build query with similarity search
        query = select(
            VectorStore,
            # Calculate cosine similarity using pgvector
            (1 - func.cosine_distance(VectorStore.embedding, embedding_str)).label('similarity')
        ).where(
            VectorStore.creator_id == creator_id
        ).where(
            (1 - func.cosine_distance(VectorStore.embedding, embedding_str)) >= similarity_threshold
        ).order_by(
            func.cosine_distance(VectorStore.embedding, embedding_str)
        ).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        rows = result.all()
        
        # Return tuples of (conversation, similarity_score)
        return [(row[0], float(row[1])) for row in rows]

    async def get_style_examples_by_category(
        self,
        creator_id: int,
        category: str,
        limit: int = 10
    ) -> List[StyleExample]:
        """Get style examples filtered by category"""
        
        query = select(StyleExample).where(
            StyleExample.creator_id == creator_id,
            StyleExample.category == category
        ).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_response_examples_by_category(
        self,
        creator_id: int,
        category: str,
        limit: int = 10
    ) -> List[ResponseExample]:
        """Get response examples filtered by category"""
        
        query = select(ResponseExample).where(
            ResponseExample.creator_id == creator_id,
            ResponseExample.category == category
        ).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_style_example(self, example_id: int, creator_id: int) -> bool:
        """Delete a style example"""
        
        query = select(StyleExample).where(
            StyleExample.id == example_id,
            StyleExample.creator_id == creator_id
        )
        result = await self.session.execute(query)
        example = result.scalar_one_or_none()
        
        if example:
            await self.session.delete(example)
            await self.session.commit()
            return True
        
        return False

    async def delete_response_example(self, example_id: int, creator_id: int) -> bool:
        """Delete a response example and all associated responses"""
        
        query = select(ResponseExample).where(
            ResponseExample.id == example_id,
            ResponseExample.creator_id == creator_id
        )
        result = await self.session.execute(query)
        example = result.scalar_one_or_none()
        
        if example:
            await self.session.delete(example)
            await self.session.commit()
            return True
        
        return False

    async def bulk_store_style_examples(
        self,
        creator_id: int,
        examples: List[dict]
    ) -> List[StyleExample]:
        """Bulk store style examples"""
        
        stored_examples = []
        
        for example_data in examples:
            example = StyleExample(
                creator_id=creator_id,
                fan_message=example_data['fan_message'],
                creator_response=example_data['creator_response'],
                category=example_data.get('category'),
                embedding=example_data['embedding']
            )
            self.session.add(example)
            stored_examples.append(example)
        
        # Commit all at once
        await self.session.commit()
        
        # Refresh all examples
        for example in stored_examples:
            await self.session.refresh(example)
        
        return stored_examples

    async def bulk_store_response_examples(
        self,
        creator_id: int,
        examples: List[dict]
    ) -> List[ResponseExample]:
        """Bulk store response examples"""
        
        stored_examples = []
        
        for example_data in examples:
            # Create the main example
            example = ResponseExample(
                creator_id=creator_id,
                fan_message=example_data['fan_message'],
                category=example_data.get('category'),
                embedding=example_data['embedding']
            )
            self.session.add(example)
            
            # Flush to get the ID
            await self.session.flush()
            
            # Create responses
            responses = example_data.get('responses', [])
            rankings = example_data.get('rankings', [])
            
            for i, response_text in enumerate(responses):
                ranking = rankings[i] if i < len(rankings) else None
                creator_response = CreatorResponse(
                    example_id=example.id,
                    response_text=response_text,
                    ranking=ranking
                )
                self.session.add(creator_response)
            
            stored_examples.append(example)
        
        # Commit all at once
        await self.session.commit()
        
        # Refresh all examples
        for example in stored_examples:
            await self.session.refresh(example)
        
        return stored_examples

    async def update_similarity_scores(self, creator_id: int, embedding: List[float]):
        """Update similarity scores for all vector store items for a creator"""
        
        # Convert embedding to string format for SQL
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # Update similarity scores using raw SQL for performance
        update_query = text("""
            UPDATE vector_store 
            SET similarity_score = (1 - (embedding <=> :embedding::vector))
            WHERE creator_id = :creator_id
        """)
        
        await self.session.execute(
            update_query, 
            {"embedding": embedding_str, "creator_id": creator_id}
        )
        await self.session.commit()

    async def get_statistics(self, creator_id: Optional[int] = None) -> dict:
        """Get statistics about stored examples for a creator or all creators"""
        
        # Count style examples
        style_count_query = select(func.count(StyleExample.id))
        if creator_id:
            style_count_query = style_count_query.where(StyleExample.creator_id == creator_id)
        
        style_count_result = await self.session.execute(style_count_query)
        style_count = style_count_result.scalar() or 0
        
        # Count response examples
        response_count_query = select(func.count(ResponseExample.id))
        if creator_id:
            response_count_query = response_count_query.where(ResponseExample.creator_id == creator_id)
        
        response_count_result = await self.session.execute(response_count_query)
        response_count = response_count_result.scalar() or 0
        
        # Count vector store items
        vector_count_query = select(func.count(VectorStore.id))
        if creator_id:
            vector_count_query = vector_count_query.where(VectorStore.creator_id == creator_id)
        
        vector_count_result = await self.session.execute(vector_count_query)
        vector_count = vector_count_result.scalar() or 0
        
        # Get categories for style examples
        style_categories_query = select(StyleExample.category).distinct()
        if creator_id:
            style_categories_query = style_categories_query.where(
                StyleExample.creator_id == creator_id,
                StyleExample.category.is_not(None)
            )
        else:
            style_categories_query = style_categories_query.where(StyleExample.category.is_not(None))
            
        style_categories_result = await self.session.execute(style_categories_query)
        style_categories = [row[0] for row in style_categories_result.all()]
        
        # Get categories for response examples
        response_categories_query = select(ResponseExample.category).distinct()
        if creator_id:
            response_categories_query = response_categories_query.where(
                ResponseExample.creator_id == creator_id,
                ResponseExample.category.is_not(None)
            )
        else:
            response_categories_query = response_categories_query.where(ResponseExample.category.is_not(None))
            
        response_categories_result = await self.session.execute(response_categories_query)
        response_categories = [row[0] for row in response_categories_result.all()]
        
        return {
            "creator_id": creator_id,
            "style_examples_count": style_count,
            "response_examples_count": response_count,
            "vector_store_count": vector_count,
            "total_examples": style_count + response_count + vector_count,
            "style_categories": style_categories,
            "response_categories": response_categories,
            "all_categories": list(set(style_categories + response_categories))
        }

    async def clear_vectors(self, creator_id: Optional[int] = None) -> dict:
        """Clear stored vectors (conversations and examples), optionally for a specific creator"""
        
        deleted_counts = {
            "style_examples": 0,
            "response_examples": 0,
            "vector_store": 0
        }
        
        # Delete style examples
        style_query = select(StyleExample)
        if creator_id:
            style_query = style_query.where(StyleExample.creator_id == creator_id)
        
        style_result = await self.session.execute(style_query)
        style_examples = style_result.scalars().all()
        
        for example in style_examples:
            await self.session.delete(example)
            deleted_counts["style_examples"] += 1
        
        # Delete response examples
        response_query = select(ResponseExample)
        if creator_id:
            response_query = response_query.where(ResponseExample.creator_id == creator_id)
        
        response_result = await self.session.execute(response_query)
        response_examples = response_result.scalars().all()
        
        for example in response_examples:
            await self.session.delete(example)
            deleted_counts["response_examples"] += 1
        
        # Delete vector store items
        vector_query = select(VectorStore)
        if creator_id:
            vector_query = vector_query.where(VectorStore.creator_id == creator_id)
        
        vector_result = await self.session.execute(vector_query)
        vector_items = vector_result.scalars().all()
        
        for item in vector_items:
            await self.session.delete(item)
            deleted_counts["vector_store"] += 1
        
        # Commit all deletions
        await self.session.commit()
        
        return deleted_counts