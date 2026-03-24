"""
LLM Client Module

Abstracts LLM API calls for easy provider switching.
Currently uses Google Gemini, but can be swapped for OpenAI, local models, etc.
"""

import httpx
from typing import Optional
from app.config import settings
from app.llm.budget import get_default_prompt_budget


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
        self.default_budget = get_default_prompt_budget()

    def _build_generate_url(self) -> str:
        return f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

    def _build_count_tokens_url(self) -> str:
        return f"{self.base_url}/models/{self.model}:countTokens?key={self.api_key}"

    @staticmethod
    def _build_prompt_body(prompt: str) -> dict:
        return {"contents": [{"parts": [{"text": prompt}]}]}

    @staticmethod
    def _estimate_tokens_fallback(prompt: str) -> int:
        # Conservative heuristic used only if provider token counting is unavailable.
        text = prompt.strip()
        if not text:
            return 0
        return max(1, len(text) // 4)

    def estimate_tokens(self, prompt: str) -> int:
        """Cheap local token estimate for pre-filtering before exact prompt building."""

        return self._estimate_tokens_fallback(prompt)

    def count_tokens(self, prompt: str) -> int:
        """Count prompt tokens using Gemini's countTokens endpoint with safe fallback."""
        url = self._build_count_tokens_url()
        headers = {"Content-Type": "application/json"}
        body = self._build_prompt_body(prompt)

        try:
            response = httpx.post(url, headers=headers, json=body, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                total_tokens = data.get("totalTokens")
                if isinstance(total_tokens, int):
                    return total_tokens
            else:
                print(f"LLM countTokens error: {response.status_code} - {response.text}")
        except httpx.RequestError as e:
            print(f"LLM countTokens request error: {e}")
        except (ValueError, TypeError) as e:
            print(f"LLM countTokens parse error: {e}")

        return self._estimate_tokens_fallback(prompt)

    async def count_tokens_async(self, prompt: str) -> int:
        """Async token counting using Gemini's countTokens endpoint with safe fallback."""
        url = self._build_count_tokens_url()
        headers = {"Content-Type": "application/json"}
        body = self._build_prompt_body(prompt)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=body)

            if response.status_code == 200:
                data = response.json()
                total_tokens = data.get("totalTokens")
                if isinstance(total_tokens, int):
                    return total_tokens
            else:
                print(f"LLM countTokens error: {response.status_code} - {response.text}")
        except httpx.RequestError as e:
            print(f"LLM countTokens request error: {e}")
        except (ValueError, TypeError) as e:
            print(f"LLM countTokens parse error: {e}")

        return self._estimate_tokens_fallback(prompt)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input text prompt
            temperature: Sampling temperature (0.0-1.0). Lower = more deterministic.
            max_output_tokens: Optional explicit completion budget override.
            
        Returns:
            Generated text response, or None if error
        """
        url = self._build_generate_url()
        headers = {"Content-Type": "application/json"}
        output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else self.default_budget.reserved_output_tokens
        )
        
        body = {
            **self._build_prompt_body(prompt),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": output_tokens,
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
    
    async def generate_async(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Async version of generate().
        
        Args:
            prompt: The input text prompt
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Optional explicit completion budget override.
            
        Returns:
            Generated text response, or None if error
        """
        url = self._build_generate_url()
        headers = {"Content-Type": "application/json"}
        output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else self.default_budget.reserved_output_tokens
        )
        
        body = {
            **self._build_prompt_body(prompt),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": output_tokens,
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

