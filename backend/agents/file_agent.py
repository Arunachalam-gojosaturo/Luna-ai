import os
import glob
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent

class FileAgent(BaseAgent):
    """
    Handles file system operations (read, write, search, list).
    """
    async def execute(self, command: str, *args, **kwargs) -> Dict[str, Any]:
        cmd_lower = command.lower().strip()
        target_file = kwargs.get("target_file", "")
        operation = kwargs.get("operation", "")

        # Extract file path: skip command keywords ("read", "file", "cat", "open", "view", "the", "show", "list")
        if not target_file:
            words = command.split()
            cleaned_words = [w.strip("'\"") for w in words if w.lower() not in ["read", "file", "files", "cat", "open", "view", "the", "show", "list", "ls", "dir"]]
            if cleaned_words:
                target_file = cleaned_words[0]

        try:
            if any(k in cmd_lower for k in ["list", "ls", "dir"]):
                path = target_file or "."
                entries = os.listdir(path)
                preview = "\n".join(entries[:30])
                if len(entries) > 30:
                    preview += f"\n... and {len(entries) - 30} more items"
                return {
                    "success": True,
                    "stdout": f"Contents of {os.path.abspath(path)}:\n{preview}",
                    "stderr": "",
                    "action": "FILE_OPERATION",
                    "sysCommand": f"ls -la {path}"
                }
            elif any(k in cmd_lower for k in ["read", "cat", "view"]) and target_file:
                if os.path.exists(target_file):
                    if os.path.isfile(target_file):
                        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read(4000)
                        return {
                            "success": True,
                            "stdout": f"Content of {target_file}:\n{content}",
                            "stderr": "",
                            "action": "FILE_OPERATION",
                            "sysCommand": f"cat {target_file}"
                        }
                    else:
                        return {
                            "success": False,
                            "stdout": "",
                            "stderr": f"'{target_file}' is a directory, not a file.",
                            "action": "FILE_OPERATION",
                            "sysCommand": ""
                        }
                else:
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": f"File '{target_file}' not found.",
                        "action": "FILE_OPERATION",
                        "sysCommand": ""
                    }
            elif any(k in cmd_lower for k in ["search", "find"]):
                pattern = target_file or "*"
                matches = glob.glob(f"**/{pattern}", recursive=True)[:20]
                return {
                    "success": True,
                    "stdout": f"Found {len(matches)} matches for '{pattern}':\n" + "\n".join(matches),
                    "stderr": "",
                    "action": "FILE_OPERATION",
                    "sysCommand": f"find . -name '{pattern}'"
                }
            else:
                return {
                    "success": True,
                    "stdout": f"File operation processed for: {target_file or command}",
                    "stderr": "",
                    "action": "FILE_OPERATION",
                    "sysCommand": ""
                }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"File operation error: {str(e)}",
                "action": "FILE_OPERATION",
                "sysCommand": ""
            }

    async def verify(self, execution_result: Dict[str, Any]) -> bool:
        return execution_result.get("success", False)

