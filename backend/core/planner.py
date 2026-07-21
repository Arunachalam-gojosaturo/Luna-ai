from enum import Enum
from typing import List
from pydantic import BaseModel

class ReasoningDepth(Enum):
    FAST = "fast"
    NORMAL = "normal"
    DEEP = "deep"

class ExecutionPlan(BaseModel):
    depth: ReasoningDepth
    intent: str
    steps: List[str]
    required_agents: List[str]
    requires_confirmation: bool = False

class Planner:
    """
    Creates dynamic execution plans based on user input, context, and memory.
    """
    async def create_plan(self, user_input: str, context: dict, memory: dict) -> ExecutionPlan:
        # Fast path heuristics (bypasses LLM for simple requests)
        words = user_input.lower().split()
        fast_keywords = {"what", "who", "where", "why", "how", "hello", "hi"}
        action_keywords = {"create", "debug", "install", "update", "search", "run", "make", "delete", "remove"}
        
        # Check for specialized agent keywords first
        has_specialized_keyword = any(kw in user_input.lower() for kw in ["git", "commit", "push", "pull", "file", "read", "write", "code", "package", "pacman"])
        
        # Only use fast path if short, no action keywords, AND no specialized keywords
        if len(words) < 8 and not any(kw in user_input.lower() for kw in action_keywords) and not has_specialized_keyword:
            return ExecutionPlan(
                depth=ReasoningDepth.FAST,
                intent="casual_conversation",
                steps=["respond_directly"],
                required_agents=[],
                requires_confirmation=False
            )
            
        # In a full implementation, you would use ProviderManager to ask a fast LLM for the plan.
        # For now, we use local heuristics for demonstration.
        
        intent = "general_task"
        agents = []
        requires_conf = False
        depth = ReasoningDepth.NORMAL
        
        # Check for package management
        if ("remove" in user_input or "uninstall" in user_input or "delete" in user_input or "rm -rf" in user_input):
            intent = "package_management"
            agents.append("package_manager")
            requires_conf = True
        elif ("install" in user_input or "search" in user_input or "package" in user_input):
            intent = "package_management"
            agents.append("package_manager")
            requires_conf = False
        elif "pacman" in user_input or "update" in user_input or "system" in user_input:
            intent = "system_management"
            agents.append("linux")
            requires_conf = False
        
        if "git" in user_input or "commit" in user_input or "push" in user_input:
            intent = "git_operation"
            agents.append("git")
            
        if "file" in user_input or "read" in user_input or "write" in user_input or "code" in user_input:
            intent = "file_operation"
            agents.append("file")
            
        if "complex" in user_input or "analyze" in user_input or len(action_keywords.intersection(set(words))) > 1:
            depth = ReasoningDepth.DEEP
            
        if not agents:
            agents.append("linux") # Default fallback agent

        return ExecutionPlan(
            depth=depth,
            intent=intent,
            steps=[f"Analyze intent: {intent}", f"Invoke {', '.join(agents)} agents", "Verify result"],
            required_agents=agents,
            requires_confirmation=requires_conf
        )

# Singleton instance
planner = Planner()
