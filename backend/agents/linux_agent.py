import asyncio
import datetime
import psutil

from backend.agents.base_agent import BaseAgent

class LinuxAgent(BaseAgent):
    def __init__(self):
        self.audit_log_path = "luna_audit.log"
        
    def append_audit_log(self, command: str, intent: str, sys_command: str, privilege: bool):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] INTENT: {intent} | PRIVILEGE: {privilege} | CMD: {command} | EXEC: {sys_command}\n"
        with open(self.audit_log_path, "a") as f:
            f.write(log_entry)

    def validate_command(self, command: str):
        if "rm -rf /" in command:
            return {"allowed": False, "reason": "Destructive command"}
        return {"allowed": True, "wrappedCommand": command}

    async def execute(self, command: str, category: str):
        self.append_audit_log(command, category, command, "sudo" in command or "pkexec" in command)
        val = self.validate_command(command)
        if not val["allowed"]:
            return {"success": False, "stdout": "", "stderr": val["reason"]}
        
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
