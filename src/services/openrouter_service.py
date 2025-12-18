
import os
import httpx
import json
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)

class OpenRouterService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": settings.app_name, # Optional: Site URL
            "X-Title": settings.app_name, # Optional: Site Title
            "Content-Type": "application/json"
        }

    async def generate_content(self, prompt: str, temperature: float = 0.1, max_tokens: int = 500) -> str:
        """
        Generate content using OpenRouter API
        """
        if not self.api_key:
             raise ValueError("OpenRouter API Key is missing. Please set OPENROUTER_API_KEY in .env")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            # trust_env=False prevents checking for system proxies which often causes getaddrinfo failed on some setups
            async with httpx.AsyncClient(trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenRouter API Error: {response.status_code} - {response.text}")
                    raise Exception(f"OpenRouter API Error: {response.status_code} - {response.text}")
                
                data = response.json()
                # OpenRouter (OpenAI compatible) response structure
                return data['choices'][0]['message']['content']

        except Exception as e:
            logger.error(f"Error calling OpenRouter: {str(e)}")
            raise