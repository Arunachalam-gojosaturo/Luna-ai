import asyncio
import datetime
import psutil
import shlex
import re

from backend.agents.base_agent import BaseAgent

class LinuxAgent(BaseAgent):
    def __init__(self):
        self.audit_log_path = "luna_audit.log"
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
        val = self.validate_command(command)
        if not val or not val.get("allowed", False):
            return {"success": False, "stdout": "", "stderr": val.get("reason", "Command validation failed") if val else "Invalid validation response"}
        
        try:
            proc = await asyncio.create_subprocess_shell(
                val["wrappedCommand"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
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
