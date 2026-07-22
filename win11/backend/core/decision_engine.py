from typing import List, Dict, Any
from pydantic import BaseModel

class VerificationResult(BaseModel):
    success: bool
    error: str = ""
    retry_needed: bool = False

class DecisionEngine:
    """
    Handles Tool Selection, Verification and maps Planner output to Agents.
    """
    def __init__(self):
        self.fast_keywords = ["hello", "hi", "time", "battery", "thanks", "open"]
        self.deep_keywords = ["debug", "architect", "code", "workflow", "optimize"]

    async def verify_execution(self, execution_data: Dict[str, Any]) -> VerificationResult:
        """
        Self-correction loop. Validates if the tool execution succeeded.
        """
        # If execution data is missing or has a catastrophic failure
        if not execution_data:
            return VerificationResult(success=False, error="No execution data returned.")

        status = execution_data.get("status", "error")
        if status == "success":
            return VerificationResult(success=True)
            
        stderr = execution_data.get("stderr", "")
        # Heuristics for common errors
        if "permission denied" in stderr.lower():
            return VerificationResult(success=False, error="Permission denied.", retry_needed=True)
        if "not found" in stderr.lower():
            return VerificationResult(success=False, error="Command or file not found.", retry_needed=False)
            
        return VerificationResult(success=False, error=stderr or "Unknown error", retry_needed=False)

decision_engine = DecisionEngine()
