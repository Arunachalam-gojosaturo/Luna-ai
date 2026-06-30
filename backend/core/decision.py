from typing import List, Dict, Any

class DecisionEngine:
    """
    Handles Intent Detection, Adaptive Reasoning Depth, and Tool Selection.
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
        # A lightweight intent router (In production, could be an LLM classification call)
        cmd = command.lower()
        if "open" in cmd or "search" in cmd and "http" in cmd:
            return "BROWSER_ACTION"
        elif "install" in cmd or "update" in cmd or "pacman" in cmd:
            return "SYSTEM_MANAGEMENT"
        elif "git" in cmd or "commit" in cmd or "push" in cmd:
            return "GITHUB_ACTION"
        elif "play" in cmd or "pause" in cmd or "spotify" in cmd:
            return "MEDIA_ACTION"
        elif "file" in cmd or "directory" in cmd or "folder" in cmd or "read" in cmd:
            return "FILE_OPERATION"
        return "GENERAL_CHAT"

decision_engine = DecisionEngine()
