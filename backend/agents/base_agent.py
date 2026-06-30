from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.
    """
    
    @abstractmethod
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Executes the agent's specific task.
        Returns a dictionary with 'status', 'stdout', 'stderr', etc.
        """
        pass

    @abstractmethod
    async def verify(self, execution_result: Dict[str, Any]) -> bool:
        """
        Agent-specific verification logic.
        """
        pass
