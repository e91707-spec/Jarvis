import os
import httpx
import json
from typing import List, Dict, Optional

class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
    
    async def chat_completion(self, messages: List[Dict[str, str]], stream: bool = False, json_mode: bool = False) -> str:
        """Send chat completion request to Groq API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"Groq API error: {response.status_code} - {response.text}"
                print(error_msg, flush=True)
                raise Exception(error_msg)
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def chat_completion_sync(self, messages: List[Dict[str, str]], stream: bool = False, json_mode: bool = False) -> str:
        """Synchronous version of chat completion"""
        import asyncio
        
        async def _chat_completion():
            return await self.chat_completion(messages, stream, json_mode)
        
        return asyncio.run(_chat_completion())

# Global instance
groq_client = GroqClient()
