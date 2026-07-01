"""
Google Gemini provider implementation.
"""

import httpx
import json
from typing import AsyncIterator, Optional
from .base import BaseProvider, Message, ChatResponse


class GeminiProvider(BaseProvider):
    """Google Gemini API provider."""
    
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-pro"
    
    AVAILABLE_MODELS = [
        "gemini-pro",
        "gemini-pro-vision",
    ]
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize Gemini provider."""
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
                    f"{self.API_URL}/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [
                            {
                                "role": "user" if m.role == "user" else "model",
                                "parts": [{"text": m.content}]
                            }
                            for m in messages
                        ],
                        "generationConfig": {
                            "temperature": kwargs.get("temperature", 0.7),
                            "maxOutputTokens": kwargs.get("max_tokens", 2000),
                        }
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return ChatResponse(
                    content=content,
                    model=self.model,
                    stop_reason=data["candidates"][0].get("finishReason")
                )
            except httpx.HTTPError as e:
                raise Exception(f"Gemini API error: {str(e)}")
    
    async def stream_chat(
        self,
        messages: list[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from Gemini."""
        # Gemini doesn't support streaming in the same way, so we'll do regular chat
        response = await self.chat(messages, **kwargs)
        for char in response.content:
            yield char
    
    async def test_connection(self) -> bool:
        """Test Gemini API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.API_URL}/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": "test"}]
                            }
                        ],
                        "generationConfig": {"maxOutputTokens": 1}
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def get_available_models(self) -> list[str]:
        """Get available models."""
        return self.AVAILABLE_MODELS
