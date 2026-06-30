from backend.agents.linux_agent import LinuxAgent
from backend.agents.file_agent import FileAgent
from backend.agents.git_agent import GitAgent
from backend.agents.package_manager import package_manager_agent

class ToolRegistry:
    """
    Dynamic tool catalog where agents expose their capabilities.
    """
    def __init__(self):
        self.agents = {
            "linux": LinuxAgent(),
            "file": FileAgent(),
            "git": GitAgent(),
            "package_manager": package_manager_agent
        }

    def get_agent(self, name: str):
        return self.agents.get(name)

tool_registry = ToolRegistry()
