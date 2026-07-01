"""
Ollama local provider implementation.
"""

import httpx
import json
from typing import AsyncIterator, Optional
from .base import BaseProvider, Message, ChatResponse


class OllamaProvider(BaseProvider):
    """Ollama local AI provider."""
    
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "mistral"
    
    AVAILABLE_MODELS = [
        "mistral",
        "neural-chat",
        "starling-lm",
        "orca-mini",
        "dolphin-mixtral",
    ]
    
    def __init__(self, api_key: str = "", **kwargs):
        """Initialize Ollama provider."""
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get("base_url", self.DEFAULT_BASE_URL)
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
                    f"{self.base_url}/api/chat",
                    json={
                        "model": kwargs.get("model", self.model),
                        "messages": [
                            {"role": m.role, "content": m.content}
                            for m in messages
                        ],
                        "stream": False,
                        "options": {
                            "temperature": kwargs.get("temperature", 0.7),
                            "num_predict": kwargs.get("max_tokens", 2000),
                        }
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                return ChatResponse(
                    content=data["message"]["content"],
                    model=self.model,
                    stop_reason=data.get("done_reason")
                )
            except httpx.HTTPError as e:
                raise Exception(f"Ollama API error: {str(e)}")
    
    async def stream_chat(
        self,
        messages: list[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from Ollama."""
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": kwargs.get("model", self.model),
                        "messages": [
                            {"role": m.role, "content": m.content}
                            for m in messages
                        ],
                        "stream": True,
                        "options": {
                            "temperature": kwargs.get("temperature", 0.7),
                            "num_predict": kwargs.get("max_tokens", 2000),
                        }
                    },
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"]
                        except json.JSONDecodeError:
                            pass
            except httpx.HTTPError as e:
                raise Exception(f"Ollama stream error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test Ollama API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def get_available_models(self) -> list[str]:
        """Get available models."""
        return self.AVAILABLE_MODELS
