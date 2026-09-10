"""
Re-export DecisionEngine from backend.core.decision_engine to prevent duplicate logic.
"""
from backend.core.decision_engine import DecisionEngine, decision_engine

__all__ = ["DecisionEngine", "decision_engine"]

