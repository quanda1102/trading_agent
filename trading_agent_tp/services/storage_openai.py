"""
OpenAI Services Storage Adapter

Provides OpenAI-based services for AI memory and embeddings.
"""

from typing import List, Dict, Any, Optional
import openai
from datetime import datetime


class OpenAIServices:
    """OpenAI services adapter for AI memory."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def summarize_context(self, context: str, max_tokens: int = 500) -> str:
        """Summarize conversation context."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Summarize the following conversation context concisely:"},
                    {"role": "user", "content": context}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"Error summarizing context: {e}")
            return context[:max_tokens]  # Fallback to truncation
    
    def extract_key_points(self, conversation: str) -> List[str]:
        """Extract key points from conversation."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract the key points from this conversation as a bulleted list:"},
                    {"role": "user", "content": conversation}
                ],
                max_tokens=300,
                temperature=0.2
            )
            content = response.choices[0].message.content or ""
            # Parse bullet points
            points = [line.strip() for line in content.split('\n') if line.strip().startswith('-')]
            return points
        except Exception as e:
            print(f"Error extracting key points: {e}")
            return []
    
    def generate_memory_summary(self, interactions: List[Dict[str, Any]]) -> str:
        """Generate a summary of user interactions."""
        if not interactions:
            return "No previous interactions."
        
        # Combine recent interactions
        context = "\n".join([
            f"{interaction.get('role', 'user')}: {interaction.get('content', '')}"
            for interaction in interactions[-10:]  # Last 10 interactions
        ])
        
        return self.summarize_context(context)
