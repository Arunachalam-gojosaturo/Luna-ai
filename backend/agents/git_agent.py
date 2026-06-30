import asyncio
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent

class GitAgent(BaseAgent):
    """
    Handles version control operations.
    """
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        cwd = kwargs.get("cwd", ".")
        git_cmd = kwargs.get("git_cmd", "status")
        
        try:
            proc = await asyncio.create_subprocess_shell(
                f"git {git_cmd}",
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "action": "GITHUB_ACTION",
                "sysCommand": f"git {git_cmd}"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "action": "GITHUB_ACTION",
                "sysCommand": ""
            }

    async def verify(self, execution_result: Dict[str, Any]) -> bool:
        return execution_result.get("success", False)
