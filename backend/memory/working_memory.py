from typing import Any, Dict

class WorkingMemory:
    """
    Maintains an in-memory ephemeral state dictionary.
    This tracks the current state of a conversation, recent errors, and active context.
    """
    def __init__(self):
        self._memory: Dict[str, Any] = {
            "current_project": None,
            "active_tasks": [],
            "recent_errors": [],
            "last_action": None,
            "session_context": {}
        }

    def update(self, key: str, value: Any):
        """Update or insert a value in the working memory."""
        self._memory[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the working memory."""
        return self._memory.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Retrieve the entire working memory."""
        return dict(self._memory)

    def clear(self):
        """Reset the working memory for a new session."""
        self._memory = {
            "current_project": None,
            "active_tasks": [],
            "recent_errors": [],
            "last_action": None,
            "session_context": {}
        }

# Singleton instance
working_memory = WorkingMemory()
