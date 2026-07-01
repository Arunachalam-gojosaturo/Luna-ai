"""
NVIDIA NIM AI provider implementation.
"""

import httpx
import json
from typing import AsyncIterator, Optional
from .base import BaseProvider, Message, ChatResponse


class NvidiaNIMProvider(BaseProvider):
    """NVIDIA NIM API provider."""
    
    API_URL = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions"
    DEFAULT_MODEL = "mistralai/mistral-7b-instruct"
    
    AVAILABLE_MODELS = [
        "mistralai/mistral-7b-instruct",
        "mistralai/mixtral-8x7b-instruct-v0.1",
        "meta-llama/llama-2-70b-chat",
        "nvidia/nemotron-3-8b-chat",
    ]
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize NVIDIA NIM provider."""
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get("model", self.DEFAULT_MODEL)
        self.function_id = kwargs.get("function_id")
    
    async def chat(
        self, 
        messages: list[Message],
        **kwargs
    ) -> ChatResponse:
        """Send chat message and get response."""
        if not self.function_id:
            raise Exception("NVIDIA NIM requires function_id configuration")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.API_URL}/{self.function_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
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
                    model=self.model,
                    stop_reason=data["choices"][0].get("finish_reason")
                )
            except httpx.HTTPError as e:
                raise Exception(f"NVIDIA NIM API error: {str(e)}")
    
    async def stream_chat(
        self,
        messages: list[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from NVIDIA NIM."""
        if not self.function_id:
            raise Exception("NVIDIA NIM requires function_id configuration")
        
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.API_URL}/{self.function_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
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
                raise Exception(f"NVIDIA NIM stream error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test NVIDIA NIM API connection."""
        if not self.function_id:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.API_URL}/{self.function_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
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
