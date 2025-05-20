# File: app/services/ai_service.py (updated)
# Path: fanfix-api/app/services/ai_service.py

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# Updated imports for langchain 0.1.0+
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.schema.messages import HumanMessage, SystemMessage
import openai

class AIService:
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.chat_model = ChatOpenAI(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=0.7
        )
        openai.api_key = api_key
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using OpenAI's embeddings API"""
        try:
            client = openai.OpenAI(api_key=self.api_key)
            # Updated for OpenAI API v1.0+
            response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise
    
    async def get_suggestions(
        self, 
        fan_message: str, 
        chat_history: List[Dict[str, str]], 
        creator_style: Optional[Dict[str, Any]],
        similar_conversations: List[Dict[str, Any]],
        num_suggestions: int = 3,
        regenerate: bool = False
    ) -> List[Dict[str, Any]]:
        """Get response suggestions using LangChain and OpenAI"""
        try:
            # Build system prompt with creator style and similar conversations
            system_prompt = self._build_system_prompt(
                creator_style, 
                similar_conversations, 
                num_suggestions,
                regenerate
            )
            
            # Format chat history
            formatted_history = []
            for msg in chat_history:
                if msg["role"] == "user":
                    formatted_history.append(HumanMessage(content=msg["content"]))
                else:
                    formatted_history.append(SystemMessage(content=msg["content"]))
                    
            # Add current message
            formatted_history.append(HumanMessage(content=fan_message))
            
            # Get response using LangChain
            response = await self.chat_model.agenerate(
                [formatted_history], 
                response_format={"type": "json_object"}
            )
            
            # Parse suggestions from the response
            suggestions = self._parse_suggestions(
                response.generations[0][0].text, 
                num_suggestions
            )
            
            return suggestions
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            raise
    
    def _build_system_prompt(
        self, 
        creator_style: Optional[Dict[str, Any]], 
        similar_conversations: List[Dict[str, Any]], 
        num_suggestions: int, 
        regenerate: bool
    ) -> str:
        # Create system prompt similar to the one in your Node.js implementation
        # This would include creator style preferences and similar conversations
        prompt = f"""# Role and Objective
You are an AI assistant for the FanFix platform that creates personalized response suggestions for creators to send to their fans. Your goal is to help creators maintain engaging conversations by generating {num_suggestions} natural-sounding replies that match their personal writing style.

# Instructions
* Generate exactly {num_suggestions} different response options
* STRONGLY PREFER multi-message responses (2-3 connected messages) over single messages
* Look for natural breaking points in longer responses (after emojis, between thoughts, questions)
* Split messages that contain multiple thoughts, questions, or tone shifts
* Match the creator's writing style precisely as described
"""
        
        # Add writing style info if available
        if creator_style:
            prompt += f"\n## Writing Style Implementation\n"
            prompt += f"* Precisely follow the provided writing style\n"
            
            if creator_style.get('caseStyle'):
                prompt += f"* Case style: {creator_style.get('caseStyle')}\n"
                
            if creator_style.get('approvedEmojis') and len(creator_style.get('approvedEmojis', [])) > 0:
                emoji_list = ', '.join(creator_style.get('approvedEmojis', []))
                prompt += f"* Approved emojis: {emoji_list}\n"
                
            if creator_style.get('textReplacements'):
                prompt += f"* Text replacements: {json.dumps(creator_style.get('textReplacements'))}\n"
                
            if creator_style.get('styleInstructions'):
                prompt += f"* Additional style guidance: {creator_style.get('styleInstructions')}\n"
                
            if creator_style.get('messageLengthPreference'):
                prompt += f"* Message length preference: {creator_style.get('messageLengthPreference')}\n"
            
        # Add example conversations if available
        if similar_conversations and len(similar_conversations) > 0:
            prompt += "\n# Example Conversations\n"
            for i, convo in enumerate(similar_conversations):
                prompt += f"\n## Example {i+1}\n"
                prompt += f"### Fan Message\n\"{convo['fanMessage']}\"\n\n"
                prompt += f"### Creator Response\n"
                for resp in convo['creatorResponses']:
                    prompt += f"\"{resp}\"\n"
        
        # Add regeneration instruction if needed
        if regenerate:
            prompt += "\n# Final Instructions\nThis is a regeneration request - provide COMPLETELY DIFFERENT suggestions than before.\n"
            
        prompt += "\nReturn only valid JSON following this structure:\n"
        prompt += """```
{
  "suggestions": [
    {
      "type": "multi",
      "messages": ["First message here 😅", "Second message continues the thought"]
    },
    {
      "type": "multi",
      "messages": ["Another approach", "With follow-up", "Maybe a third"]
    }
  ]
}
```"""
        
        return prompt
    
    def _parse_suggestions(self, content: str, requested_count: int) -> List[Dict[str, Any]]:
        """Parse JSON response from the API into suggestion format"""
        try:
            # Parse JSON response
            if isinstance(content, str):
                response_data = json.loads(content)
            else:
                response_data = content
                
            if "suggestions" in response_data and isinstance(response_data["suggestions"], list):
                suggestions = response_data["suggestions"]
                # Validate and clean suggestions
                valid_suggestions = []
                for sugg in suggestions[:requested_count]:
                    if sugg.get("type") in ["single", "multi"] and "messages" in sugg:
                        # Ensure messages is a list of strings
                        messages = [str(msg) for msg in sugg["messages"] if msg]
                        if messages:
                            valid_suggestions.append({
                                "type": sugg["type"],
                                "messages": messages
                            })
                
                return valid_suggestions
            
            # Fallback: create simple suggestions from text
            return [{"type": "single", "messages": [content.strip()]}]
        except Exception as e:
            print(f"Error parsing suggestions: {e}")
            # Fallback
            return [{"type": "single", "messages": ["I'd be happy to chat with you!"]}]