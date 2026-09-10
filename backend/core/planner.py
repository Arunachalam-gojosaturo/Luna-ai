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
    user_input: str = ""
    steps: List[str]
    required_agents: List[str]
    requires_confirmation: bool = False

class Planner:
    """
    Creates dynamic execution plans based on user input, context, and memory.
    """
    async def create_plan(self, user_input: str, context: dict, memory: dict) -> ExecutionPlan:
        text = user_input.strip()
        text_lower = text.lower()
        words = text_lower.split()

        # Check for explicit question or conversational intent
        question_starters = (
            "what", "who", "where", "when", "why", "how", "which",
            "is ", "are ", "can ", "could ", "would ", "should ",
            "do ", "does ", "did ", "tell me", "explain", "describe",
            "write ", "create a function", "generate", "summarize",
            "help me understand", "define ", "meaning of"
        )
        conversational_words = {
            "hello", "hi", "hey", "hola", "greetings", "thanks", "thank",
            "good morning", "good afternoon", "good evening", "howdy",
            "who are you", "what are you", "what is your name"
        }

        is_question = (
            text.endswith("?") or
            any(text_lower.startswith(q) for q in question_starters) or
            any(cw in text_lower for cw in conversational_words) or
            "tell me" in text_lower or
            "explain" in text_lower
        )

        # Check for explicit system/OS action commands
        action_match = False
        agents = []
        intent = "casual_conversation" if not is_question else "information_query"
        requires_conf = False
        depth = ReasoningDepth.FAST

        # 1. Developer Co-Pilot: GitHub Repo Creation, Workflow Automation & Code Debugging
        if any(k in text_lower for k in [
            "github repo", "create repo", "create a repo", "create a new repo",
            "create repository", "commit my latest changes", "commit and push",
            "developer copilot", "debug my code", "debug code", "troubleshoot error"
        ]):
            intent = "developer_copilot"
            agents.append("developer_copilot")
            action_match = True

        # 2. Package management actions (imperative only, not informational questions)
        elif not is_question:
            if any(text_lower.startswith(p) for p in ["install ", "uninstall ", "remove ", "pacman -", "yay -", "paru -"]):
                intent = "package_management"
                agents.append("package_manager")
                action_match = True
                requires_conf = any(k in text_lower for k in ["remove", "uninstall", "delete", "rm -rf"])

            # 3. Git operations (imperative)
            elif any(text_lower.startswith(g) for g in ["git ", "auto_commit", "auto commit", "auto_push", "auto push"]):
                intent = "git_operation"
                agents.append("git")
                action_match = True

            # 3. File operations (imperative)
            elif any(text_lower.startswith(f) for f in ["read file", "write file", "save to file", "create file"]):
                intent = "file_operation"
                agents.append("file")
                action_match = True

            # 4. System / Linux actions (imperative system controls)
            elif any(kw in text_lower for kw in [
                "play ", "youtube", "volume", "brightness", "screenshot",
                "unlock phone", "unlock mobile", "lock phone", "lock mobile", "mobile pin",
                "open whatsapp", "launch whatsapp", "whatsapp",
                "open firefox", "open browser", "open terminal", "open kitty", "open code", "launch code", "launch vscode",
                "open spotify", "open telegram", "open discord",
                "poweroff", "shutdown", "reboot", "restart", "suspend", "hyprlock", "killactive", "close window",
                "workspace ", "wmctrl "
            ]) or (len(words) > 0 and words[0] in ["ls", "cat", "ps", "df", "free", "uname", "htop", "run", "exec"]):
                intent = "system_management"
                agents.append("linux")
                action_match = True

        if action_match:
            depth = ReasoningDepth.NORMAL
            return ExecutionPlan(
                depth=depth,
                intent=intent,
                user_input=user_input,
                steps=[f"Analyze intent: {intent}", f"Invoke {', '.join(agents)} agents", "Verify result"],
                required_agents=agents,
                requires_confirmation=requires_conf
            )

        # For all questions, queries, conversations, writing, and explanations:
        # Route directly to LLM with no system agents!
        if len(words) > 25 or "analyze" in text_lower or "complex" in text_lower or "compare" in text_lower:
            depth = ReasoningDepth.DEEP

        return ExecutionPlan(
            depth=depth,
            intent=intent,
            user_input=user_input,
            steps=["respond_directly"],
            required_agents=[],
            requires_confirmation=False
        )

    def generate_plan(self, command: str, intent: str, reasoning_depth: str) -> List[str]:
        """Generate step-by-step plan list for brain_v2."""
        return [f"Analyze intent: {intent}", f"Execute action for request: {command}", "Verify execution result"]

# Singleton instances
planner = Planner()
planner_engine = planner

