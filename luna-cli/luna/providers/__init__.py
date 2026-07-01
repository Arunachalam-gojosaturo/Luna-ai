"""
AI Providers module.
Supports multiple AI providers with automatic routing and fallback.
"""

from .base import BaseProvider, ProviderRegistry, Message, ChatResponse
from .groq import GroqProvider
from .openai import OpenAIProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider
from .nvidia import NvidiaNIMProvider

# Register all providers
ProviderRegistry.register("groq", GroqProvider)
ProviderRegistry.register("openai", OpenAIProvider)
ProviderRegistry.register("gemini", GeminiProvider)
ProviderRegistry.register("ollama", OllamaProvider)
ProviderRegistry.register("openrouter", OpenRouterProvider)
ProviderRegistry.register("nvidia", NvidiaNIMProvider)

__all__ = [
    "BaseProvider",
    "ProviderRegistry",
    "Message",
    "ChatResponse",
    "GroqProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "OllamaProvider",
    "OpenRouterProvider",
    "NvidiaNIMProvider",
]
