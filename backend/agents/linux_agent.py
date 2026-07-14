import asyncio
import datetime
import psutil
import shlex
import re

from backend.agents.base_agent import BaseAgent

class LinuxAgent(BaseAgent):
    def __init__(self):
        self.os_type = "arch" # Explicitly designed for Arch Linux compatibility
        from backend.config.paths import get_log_dir
        self.audit_log_path = str(get_log_dir() / "luna_audit.log")
        # Whitelist of allowed command prefixes for safety
        self.allowed_commands = [
            "ls", "cat", "pwd", "cd", "echo", "mkdir", "touch", "cp", "mv", "rm",
            "find", "grep", "git", "pip", "npm", "python", "node", "curl", "wget",
            "systemctl", "sudo", "pacman", "apt", "yum", "docker", "docker-compose",
            "tmux", "screen", "less", "more", "head", "tail", "wc", "chmod", "chown",
            "ps", "kill", "df", "du", "free", "top", "htop", "uname", "whoami", "xdg-open", "open", "playerctl",
            "hyprctl", "wpctl", "ydotool", "wtype", "yay", "paru"
        ]
        
    def append_audit_log(self, command: str, intent: str, sys_command: str, privilege: bool):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] INTENT: {intent} | PRIVILEGE: {privilege} | CMD: {command} | EXEC: {sys_command}\n"
        with open(self.audit_log_path, "a") as f:
            f.write(log_entry)

    def validate_command(self, command: str):
        """Validate command for safety - check against dangerous patterns."""
        # Block destructive operations
        dangerous_patterns = [
            r"rm\s+-.*rf\s+/",  # rm -rf / style commands
            r"dd\s+if=.*of=/dev/[a-z]+",  # dd commands targeting devices
            r":\(\)\s*{\s*:\|:\s*&\s*};\s*:",  # fork bomb
            r">\s*/dev/[a-z]+",  # redirects to devices
            r";\s*rm\s+",  # chained rm commands
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {"allowed": False, "reason": f"Dangerous command pattern detected"}
        
        # Check if command starts with allowed prefix
        cmd_parts = shlex.split(command) if command else []
        if cmd_parts:
            base_cmd = cmd_parts[0].split('/')[-1]  # Get just the command name
            if base_cmd not in self.allowed_commands and not command.startswith("sudo"):
                return {"allowed": False, "reason": f"Command '{base_cmd}' not in allowed list"}
        
        return {"allowed": True, "wrappedCommand": command}

    async def execute(self, command: str, category: str):
        self.append_audit_log(command, category, command, "sudo" in command or "pkexec" in command)
        
        # Intercept common system controls and route to SystemController abstraction
        from backend.utils.sys_control import system_controller
        
        # 1. Workspace switching
        ws_match = re.search(r"workspace\s+(\d+)", command) or re.search(r"wmctrl\s+-s\s+(\d+)", command)
        if ws_match:
            num = int(ws_match.group(1))
            # wmctrl is 0-indexed, system_controller is 1-indexed
            if "wmctrl" in command:
                num += 1
            success = system_controller.switch_workspace(num)
            return {"success": success, "stdout": f"Switched to workspace {num}", "stderr": ""}

        # 2. Close Active Window
        if "killactive" in command or "windowkill" in command or "wmctrl -c" in command:
            success = system_controller.close_active_window()
            return {"success": success, "stdout": "Closed active window", "stderr": ""}

        # 3. Fullscreen
        if "fullscreen" in command:
            success = system_controller.toggle_fullscreen()
            return {"success": success, "stdout": "Toggled fullscreen", "stderr": ""}

        # 4. Volume Control
        vol_match = re.search(r"set-volume.*([\d%+-]+)", command) or re.search(r"amixer.*set.*Master.*([\d%+-]+)", command)
        if vol_match:
            change = vol_match.group(1)
            success = system_controller.set_volume(change)
            return {"success": success, "stdout": f"Volume adjusted by {change}", "stderr": ""}

        # 5. Media Control
        media_match = re.search(r"playerctl\s+(\w+)", command)
        if media_match:
            action = media_match.group(1)
            success = system_controller.control_media(action)
            return {"success": success, "stdout": f"Media command: {action}", "stderr": ""}

        val = self.validate_command(command)
        if not val or not val.get("allowed", False):
            return {"success": False, "stdout": "", "stderr": val.get("reason", "Command validation failed") if val else "Invalid validation response"}
        
        try:
            proc = await asyncio.create_subprocess_shell(
                val["wrappedCommand"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
                return {
                    "success": proc.returncode == 0,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else ""
                }
            except asyncio.TimeoutError:
                # Command is still running (e.g. xdg-open), which is a success for GUI apps
                return {
                    "success": True,
                    "stdout": "Command started in background",
                    "stderr": ""
                }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}

    def get_metrics(self):
        return {
            "cpu": psutil.cpu_percent(),
            "ram": psutil.virtual_memory().percent
        }
        
    async def verify(self, execution_result: dict) -> bool:
        return execution_result.get("success", False)

