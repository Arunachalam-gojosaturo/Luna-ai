import os
import asyncio
import psutil
import platform
import subprocess
from typing import Dict, Any

class ContextEngine:
    """
    Maintains real-time system context asynchronously.
    """
    def __init__(self):
        self._state: Dict[str, Any] = {
            "os": platform.system(),
            "release": platform.release(),
            "cpu_usage": 0.0,
            "ram_usage": 0.0,
            "disk_usage": 0.0,
            "cwd": os.getcwd(),
            "git_branch": None,
            "active_window": None,
            "battery_percent": None
        }
        self._polling_task = None
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            self._polling_task = asyncio.create_task(self._poll_state())

    def stop(self):
        self._running = False
        if self._polling_task:
            self._polling_task.cancel()

    async def _poll_state(self):
        while self._running:
            try:
                # System metrics
                self._state["cpu_usage"] = psutil.cpu_percent(interval=1.0)
                self._state["ram_usage"] = psutil.virtual_memory().percent
                self._state["disk_usage"] = psutil.disk_usage('/').percent
                
                # Battery (if available)
                battery = psutil.sensors_battery()
                self._state["battery_percent"] = battery.percent if battery else None

                # Current working directory (might change)
                self._state["cwd"] = os.getcwd()

                # Git branch (if in a git repo)
                self._state["git_branch"] = await self._get_git_branch(self._state["cwd"])

                # Active window (Hyprland IPC or fallback)
                self._state["active_window"] = await self._get_active_window()

            except Exception as e:
                # Log silently in background
                print(f"ContextEngine polling error: {e}")
            
            await asyncio.sleep(2.0) # Poll every 2 seconds

    async def _get_git_branch(self, cwd: str) -> str | None:
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "branch", "--show-current",
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0 and stdout:
                return stdout.decode().strip()
        except Exception:
            pass
        return None

    async def _get_active_window(self) -> str | None:
        # Hyprland IPC attempt (hyprctl activewindow)
        try:
            proc = await asyncio.create_subprocess_exec(
                "hyprctl", "activewindow",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0 and stdout:
                # parse out title
                for line in stdout.decode().split('\n'):
                    if line.strip().startswith("title:"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return None

    async def get_current_state(self) -> Dict[str, Any]:
        """Returns the most recently cached state."""
        return dict(self._state)

# Singleton instance
context_engine = ContextEngine()
