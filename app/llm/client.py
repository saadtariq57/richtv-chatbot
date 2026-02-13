"""
LLM Client Module

Abstracts LLM API calls for easy provider switching.
Currently uses Google Gemini, but can be swapped for OpenAI, local models, etc.
"""

import httpx
from typing import Optional
from app.config import settings


class LLMClient:
    """
    Simple LLM client with provider abstraction.
    
    Usage:
        client = LLMClient()
        response = client.generate(prompt="What is the capital of France?")
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input text prompt
            temperature: Sampling temperature (0.0-1.0). Lower = more deterministic.
            
        Returns:
            Generated text response, or None if error
        """
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }
        
        try:
            response = httpx.post(url, headers=headers, json=body, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                print(f"LLM API Error: {response.status_code} - {response.text}")
                return None
                
        except httpx.RequestError as e:
            print(f"LLM Request Error: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"Error parsing LLM response: {e}")
            return None
    
    async def generate_async(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        """
        Async version of generate().
        
        Args:
            prompt: The input text prompt
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Generated text response, or None if error
        """
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=body)
            
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                print(f"LLM API Error: {response.status_code} - {response.text}")
                return None
                
        except httpx.RequestError as e:
            print(f"LLM Request Error: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"Error parsing LLM response: {e}")
            return None


# Singleton instance for reuse across the app
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

