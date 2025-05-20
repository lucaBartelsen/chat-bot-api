import time
from typing import List, Optional, Tuple
import openai
from openai import OpenAI

from app.models.creator import Creator, CreatorStyle, StyleExample
from app.models.suggestion import SuggestionRequest, MessageSuggestion
from app.services.vector_service import VectorService

class AIService:
    """Service for AI-powered suggestion generation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
    
    async def generate_suggestions(
        self,
        request: SuggestionRequest,
        creator: Creator,
        style: CreatorStyle,
        examples: List[StyleExample],
        similar_conversations: List[Tuple[any, float]] = None,
        temperature: float = 0.7
    ) -> List[MessageSuggestion]:
        """Generate AI suggestions based on creator style and examples"""
        
        # Start timing
        start_time = time.time()
        
        # Format system message with style instructions
        system_message = self._format_system_message(creator, style)
        
        # Add examples to the system message
        system_message += self._format_examples(examples)
        
        # Add similar conversations if available
        if similar_conversations and len(similar_conversations) > 0:
            system_message += "\n\nHere are some similar conversations from the past:\n"
            for conv, similarity in similar_conversations:
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
    
    def _format_system_message(self, creator: Creator, style: CreatorStyle) -> str:
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
    
    def _format_examples(self, examples: List[StyleExample]) -> str:
        """Format examples for the system message"""
        
        if not examples or len(examples) == 0:
            return ""
        
        example_text = "\n\nHere are some examples of fan messages and how the creator responded:\n"
        
        for example in examples:
            example_text += f"\nFan: {example.fan_message}\nCreator: {example.creator_response}\n"
        
        return example_text