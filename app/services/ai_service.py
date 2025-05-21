import time
from typing import List, Optional, Tuple, Dict, Any, Union
import openai
from openai import OpenAI

from app.models.creator import (
    Creator, 
    CreatorStyle, 
    StyleExample, 
    ResponseExample,
    CreatorResponse,
    VectorStore
)
from app.models.suggestion import SuggestionRequest, MessageSuggestion
from app.services.vector_service import VectorService

class AIService:
    """Service for AI-powered suggestion generation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding vector for a text using OpenAI's API"""
        response = await self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    async def generate_suggestions(
        self,
        request: SuggestionRequest,
        creator: Creator,
        style: Optional[CreatorStyle] = None,
        style_examples: List[StyleExample] = None,
        response_examples: List[ResponseExample] = None,
        similar_conversations: List[Tuple[Any, float]] = None,
        temperature: float = 0.7
    ) -> Tuple[List[MessageSuggestion], str, float]:
        """Generate AI suggestions based on creator style and examples"""
        
        # Start timing
        start_time = time.time()
        
        # Format system message with style instructions
        system_message = self._format_system_message(creator, style)
        
        # Add style examples to the system message
        if style_examples and len(style_examples) > 0:
            system_message += self._format_style_examples(style_examples)
        
        # Add response examples if available
        if response_examples and len(response_examples) > 0:
            system_message += self._format_response_examples(response_examples)
        
        # Add similar conversations if available
        if similar_conversations and len(similar_conversations) > 0:
            system_message += "\n\nHere are some similar conversations from the past:\n"
            for conv, similarity in similar_conversations:
                if isinstance(conv, VectorStore):
                    system_message += f"\nFan: {conv.fan_message}\nCreator: {conv.creator_response}\n"
        
        # Create the messages array
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Fan message: {request.fan_message}\n\nGenerate {request.suggestion_count} different response suggestions that match the creator's style."}
        ]
        
        # Select the model to use
        model = request.model or "gpt-4"
        
        # Make API call to OpenAI
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            n=request.suggestion_count,
            max_tokens=1000
        )
        
        # Process response into suggestions
        suggestions = []
        for choice in response.choices:
            suggestions.append(
                MessageSuggestion(
                    text=choice.message.content.strip(),
                    confidence=1.0 - (choice.index * 0.1)  # Simple confidence estimation
                )
            )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return suggestions, model, processing_time
    
    def _format_system_message(self, creator: Creator, style: Optional[CreatorStyle]) -> str:
        """Format the system message with style instructions"""
        
        system_message = f"""You are an AI assistant helping to generate message suggestions for {creator.name}. 
Your task is to write responses that perfectly match {creator.name}'s writing style.

Here's information about {creator.name}'s writing style:
"""
        
        # Add style details if available
        if style:
            if style.case_style:
                system_message += f"- Case Style: {style.case_style}\n"
            
            if style.approved_emojis:
                system_message += f"- Approved Emojis: {', '.join(style.approved_emojis)}\n"
            
            if style.text_replacements:
                system_message += "- Text Replacements:\n"
                for original, replacement in style.text_replacements.items():
                    system_message += f"  * Replace '{original}' with '{replacement}'\n"
            
            if style.common_abbreviations:
                system_message += "- Common Abbreviations:\n"
                for abbr, full in style.common_abbreviations.items():
                    system_message += f"  * {abbr} = {full}\n"
            
            if style.message_length_preferences:
                system_message += "- Message Length Preferences:\n"
                for k, v in style.message_length_preferences.items():
                    system_message += f"  * {k}: {v}\n"
            
            if style.style_instructions:
                system_message += f"\nAdditional Style Instructions:\n{style.style_instructions}\n"
            
            if style.tone_range:
                system_message += f"- Tone Range: {', '.join(style.tone_range)}\n"
        
        return system_message
    
    def _format_style_examples(self, examples: List[StyleExample]) -> str:
        """Format style examples for the system message"""
        
        if not examples or len(examples) == 0:
            return ""
        
        example_text = "\n\nHere are some examples of fan messages and how the creator responded " \
                       "(these show the creator's writing style):\n"
        
        for example in examples:
            example_text += f"\nFan: {example.fan_message}\nCreator: {example.creator_response}\n"
        
        return example_text
    
    def _format_response_examples(self, examples: List[ResponseExample]) -> str:
        """Format response examples for the system message"""
        
        if not examples or len(examples) == 0:
            return ""
        
        example_text = "\n\nHere are some examples of fan messages with multiple possible " \
                       "response options (higher ranking indicates better responses):\n"
        
        for example in examples:
            example_text += f"\nFan: {example.fan_message}\n"
            
            # Sort responses by ranking (higher is better)
            sorted_responses = sorted(example.responses, key=lambda r: r.ranking or 0, reverse=True)
            
            for i, response in enumerate(sorted_responses):
                ranking_indicator = "*" * (response.ranking or (len(sorted_responses) - i))
                example_text += f"Response Option {i+1} {ranking_indicator}: {response.response_text}\n"
            
            example_text += "\n"
        
        return example_text
    
    async def find_and_use_examples(
        self,
        request: SuggestionRequest,
        creator: Creator,
        style: Optional[CreatorStyle],
        vector_service: VectorService,
        similarity_threshold: float = 0.7,
        style_examples_limit: int = 3,
        response_examples_limit: int = 2
    ) -> Tuple[List[MessageSuggestion], str, float]:
        """Find relevant examples and use them to generate suggestions"""
        
        try:
            # Generate embedding for fan message
            embedding = await self.generate_embedding(request.fan_message)
            
            # Find similar style examples
            similar_style_examples = await vector_service.find_similar_style_examples(
                creator_id=creator.id,
                embedding=embedding,
                similarity_threshold=similarity_threshold,
                limit=style_examples_limit
            )
            style_examples = [ex for ex, _ in similar_style_examples]
            
            # Find similar response examples
            similar_response_examples = await vector_service.find_similar_response_examples(
                creator_id=creator.id,
                embedding=embedding,
                similarity_threshold=similarity_threshold,
                limit=response_examples_limit
            )
            response_examples = [ex for ex, _ in similar_response_examples]
            
            # Find similar conversations from vector store
            similar_conversations = await vector_service.find_similar_conversations(
                creator_id=creator.id,
                embedding=embedding,
                similarity_threshold=similarity_threshold,
                limit=3
            )
            
            # Generate suggestions using all found examples
            return await self.generate_suggestions(
                request=request,
                creator=creator,
                style=style,
                style_examples=style_examples,
                response_examples=response_examples,
                similar_conversations=similar_conversations,
                temperature=0.7
            )
            
        except Exception as e:
            # Log error and fall back to basic generation
            print(f"Error finding examples: {str(e)}")
            return await self.generate_suggestions(
                request=request,
                creator=creator,
                style=style,
                temperature=0.7
            )