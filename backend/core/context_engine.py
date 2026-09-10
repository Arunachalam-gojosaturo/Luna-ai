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
        distro = "Arch Linux"
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            distro = line.split("=", 1)[1].strip().strip('"')
                            break
        except Exception:
            pass

        self._state: Dict[str, Any] = {
            "os": distro,
            "distribution": "Arch Linux",
            "release": platform.release(),
            "desktop": os.environ.get("XDG_CURRENT_DESKTOP", "Hyprland (Wayland)"),
            "cpu_usage": 0.0,
            "ram_usage": 0.0,
            "disk_usage": 0.0,
            "cwd": os.getcwd(),
            "git_branch": None,
            "active_window": None,
            "battery_percent": None,
            "mobile_connected": False,
            "mobile_status": "Disconnected"
        }
        self.working_memory: Dict[str, Any] = {
            "current_project": None,
            "current_directory": os.getcwd(),
            "active_tasks": [],
            "recent_errors": []
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
        from backend.utils.adb_manager import adb_manager
        while self._running:
            try:
                # System metrics (non-blocking)
                self._state["cpu_usage"] = await asyncio.to_thread(psutil.cpu_percent, None)
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

                # Mobile ADB connection check
                is_connected = await adb_manager.is_device_connected()
                self._state["mobile_connected"] = is_connected
                self._state["mobile_status"] = "Connected" if is_connected else "Disconnected (No mobile device detected via ADB)"

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
        # Hyprland IPC attempt (hyprctl activewindow -j)
        try:
            proc = await asyncio.create_subprocess_exec(
                "hyprctl", "activewindow", "-j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0 and stdout:
                try:
                    data = json.loads(stdout.decode())
                    if isinstance(data, dict):
                        title = data.get("title", "")
                        cls = data.get("class", "")
                        return f"{cls}: {title}" if cls and title else (title or cls or None)
                except Exception:
                    pass
                for line in stdout.decode().split('\n'):
                    if line.strip().startswith("title:"):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return None

    async def get_current_state(self) -> Dict[str, Any]:
        """Returns the most recently cached state with fresh mobile connection status."""
        try:
            from backend.utils.adb_manager import adb_manager
            is_connected = await adb_manager.is_device_connected()
            self._state["mobile_connected"] = is_connected
            self._state["mobile_status"] = "Connected" if is_connected else "Disconnected (No mobile device detected via ADB)"
        except Exception:
            pass
        return dict(self._state)

    def get_system_context(self) -> dict:
        """Synchronous snapshot for compatibility with context.py callers."""
        return {
            "os": self._state.get("os", "Arch Linux"),
            "release": self._state.get("release", ""),
            "cpu_usage": self._state.get("cpu_usage", 0.0),
            "ram_usage": self._state.get("ram_usage", 0.0),
            "disk_usage": self._state.get("disk_usage", 0.0),
            "cwd": os.getcwd(),
            "working_memory": self.working_memory
        }

    def update_working_memory(self, key: str, value: Any):
        """Update working memory entry."""
        self.working_memory[key] = value


# Singleton instance
context_engine = ContextEngine()
