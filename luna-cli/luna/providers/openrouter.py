"""
OpenRouter AI provider implementation.
"""

import httpx
import json
from typing import AsyncIterator, Optional
from .base import BaseProvider, Message, ChatResponse


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider."""
    
    API_URL = "https://openrouter.io/api/v1"
    DEFAULT_MODEL = "meta-llama/llama-2-70b-chat"
    
    AVAILABLE_MODELS = [
        "meta-llama/llama-2-70b-chat",
        "mistralai/mistral-7b-instruct",
        "nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
        "openchat/openchat-7b",
        "undi95/toppy-m-7b",
    ]
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize OpenRouter provider."""
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get("model", self.DEFAULT_MODEL)
    
    async def chat(
        self, 
        messages: list[Message],
        **kwargs
    ) -> ChatResponse:
        """Send chat message and get response."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.API_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://luna-cli.io",
                    },
                    json={
                        "model": kwargs.get("model", self.model),
                        "messages": [
                            {"role": m.role, "content": m.content}
                            for m in messages
                        ],
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 2000),
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                return ChatResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data["model"],
                    stop_reason=data["choices"][0].get("finish_reason")
                )
            except httpx.HTTPError as e:
                raise Exception(f"OpenRouter API error: {str(e)}")
    
    async def stream_chat(
        self,
        messages: list[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from OpenRouter."""
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.API_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://luna-cli.io",
                    },
                    json={
                        "model": kwargs.get("model", self.model),
                        "messages": [
                            {"role": m.role, "content": m.content}
                            for m in messages
                        ],
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 2000),
                        "stream": True,
                    },
                    timeout=30.0
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                chunk = json.loads(line[6:])
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                pass
            except httpx.HTTPError as e:
                raise Exception(f"OpenRouter stream error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test OpenRouter API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.API_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://luna-cli.io",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 1,
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def get_available_models(self) -> list[str]:
        """Get available models."""
        return self.AVAILABLE_MODELS
