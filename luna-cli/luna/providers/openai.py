"""
OpenAI provider implementation.
"""

import httpx
import json
from typing import AsyncIterator, Optional
from .base import BaseProvider, Message, ChatResponse


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""
    
    API_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4-turbo-preview"
    
    AVAILABLE_MODELS = [
        "gpt-4-turbo-preview",
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize OpenAI provider."""
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
                formatted_messages = []
                for m in messages:
                    msg = {"role": m.role}
                    if m.content is not None:
                        msg["content"] = m.content
                    if m.tool_calls:
                        msg["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.name, "arguments": tc.arguments}
                            } for tc in m.tool_calls
                        ]
                    if m.tool_call_id:
                        msg["tool_call_id"] = m.tool_call_id
                    if m.name:
                        msg["name"] = m.name
                    formatted_messages.append(msg)
                
                payload = {
                    "model": kwargs.get("model", self.model),
                    "messages": formatted_messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000),
                }
                
                if "tools" in kwargs:
                    payload["tools"] = kwargs["tools"]
                    
                response = await client.post(
                    f"{self.API_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                message_data = data["choices"][0]["message"]
                from .base import ToolCall
                tool_calls = None
                if "tool_calls" in message_data:
                    tool_calls = [
                        ToolCall(
                            id=tc["id"],
                            name=tc["function"]["name"],
                            arguments=tc["function"]["arguments"]
                        ) for tc in message_data["tool_calls"]
                    ]
                
                return ChatResponse(
                    content=message_data.get("content"),
                    model=data["model"],
                    stop_reason=data["choices"][0].get("finish_reason"),
                    tool_calls=tool_calls
                )
            except httpx.HTTPError as e:
                raise Exception(f"OpenAI API error: {str(e)}")
    
    async def stream_chat(
        self,
        messages: list[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from OpenAI."""
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.API_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
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
                raise Exception(f"OpenAI stream error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.API_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
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
