import psutil
import os
import platform

class ContextEngine:
    """
    Maintains Working Memory and captures real-time system context.
    """
    def __init__(self):
        self.working_memory = {
            "current_project": None,
            "current_directory": os.getcwd(),
            "active_tasks": [],
            "recent_errors": []
        }
        
    def get_system_context(self) -> dict:
        """Fetch live system telemetry."""
        return {
            "os": platform.system(),
            "release": platform.release(),
            "cpu_usage": psutil.cpu_percent(interval=0.1),
            "ram_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "cwd": os.getcwd(),
            "working_memory": self.working_memory
        }

    def update_working_memory(self, key: str, value: any):
        self.working_memory[key] = value

context_engine = ContextEngine()
