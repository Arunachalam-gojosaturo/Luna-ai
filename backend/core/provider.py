"""
Provider module re-exporting ProviderManager from backend.providers.provider_manager.
Maintains unified multi-provider logic (Gemini, Groq, OpenRouter, GitHub, NVIDIA, Cerebras, OpenAI).
"""

from typing import Dict, Any, List
from backend.providers.provider_manager import ProviderManager as _BaseProviderManager

class ProviderManager(_BaseProviderManager):
    """
    Core ProviderManager extending the full multi-provider implementation
    with backwards-compatible aliases for legacy brain callers.
    """
    async def generate_response(self, messages: List[Dict], req) -> Dict:
        """Alias for get_json for backwards compatibility."""
        return await self.get_json(messages, req)

__all__ = ["ProviderManager"]

