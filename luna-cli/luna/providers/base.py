"""
Base provider interface for all AI providers.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ToolCall:
    """Tool call definition."""
    id: str
    name: str
    arguments: str

@dataclass
class Message:
    """Message data class."""
    role: str  # "user", "assistant", "system", "tool"
    content: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

@dataclass
class ChatResponse:
    """Chat response data class."""
    content: Optional[str] = None
    model: str = ""
    stop_reason: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None


class BaseProvider(ABC):
    """Base class for all AI providers."""
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize provider."""
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def chat(
        self, 
        messages: list[Message],
        **kwargs
    ) -> ChatResponse:
        """Send chat message and get response."""
        pass
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: list[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connection."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get available models."""
        pass


class ProviderRegistry:
    """Registry for all providers."""
    
    _providers: Dict[str, type[BaseProvider]] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: type[BaseProvider]):
        """Register a provider."""
        cls._providers[name] = provider_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type[BaseProvider]]:
        """Get provider class."""
        return cls._providers.get(name)
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all providers."""
        return list(cls._providers.keys())
