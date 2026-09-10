"""
Re-export ContextEngine from backend.core.context_engine to eliminate duplicate definitions.
"""
from backend.core.context_engine import ContextEngine, context_engine

__all__ = ["ContextEngine", "context_engine"]

