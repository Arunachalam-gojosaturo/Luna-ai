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
    def determine_reasoning_depth(self, command: str) -> str:
        cmd_lower = command.lower()
        if any(word in cmd_lower for word in self.fast_keywords) and len(command.split()) < 5:
            return "fast"
        elif any(word in cmd_lower for word in self.deep_keywords):
            return "deep"
        return "medium"

    def detect_intent(self, command: str) -> str:
        cmd = command.lower()
        if "open" in cmd or ("search" in cmd and "http" in cmd):
            return "BROWSER_ACTION"
        elif "install" in cmd or "update" in cmd or "pacman" in cmd or "yay" in cmd:
            return "SYSTEM_MANAGEMENT"
        elif "git" in cmd or "commit" in cmd or "push" in cmd:
            return "GITHUB_ACTION"
        elif "play" in cmd or "pause" in cmd or "spotify" in cmd or "youtube" in cmd:
            return "MEDIA_ACTION"
        elif "file" in cmd or "directory" in cmd or "folder" in cmd or "read" in cmd:
            return "FILE_OPERATION"
        return "GENERAL_CHAT"

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
