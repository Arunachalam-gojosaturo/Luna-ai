import asyncio
import os
import requests
import json
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent

class GitAgent(BaseAgent):
    """
    Handles version control operations including AI auto-commits.
    """
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        cwd = kwargs.get("cwd", ".")
        git_cmd = kwargs.get("git_cmd", "status")
        api_key = kwargs.get("api_key", os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY") or "")
        provider = "gemini" if os.getenv("GEMINI_API_KEY") else ("groq" if os.getenv("GROQ_API_KEY") else "openai")

        try:
            if git_cmd == "auto_commit":
                # 1. Add all files
                await self._run_subprocess("git add .", cwd)
                
                # 2. Get diff
                diff_stdout, _ = await self._run_subprocess("git diff --cached", cwd)
                if not diff_stdout.strip():
                    return self._result(True, "No changes to commit.", "", "git status")

                # 3. Generate commit message via LLM
                prompt = f"Write a concise, professional git commit message for the following diff. Only return the commit message, no markdown, no quotes.\\n\\n{diff_stdout[:3000]}"
                commit_msg = await self._generate_llm_response(prompt, api_key, provider)
                
                if not commit_msg:
                    commit_msg = "Auto-commit: Updates applied."
                
                # 4. Commit
                # Escape quotes in commit message
                safe_msg = commit_msg.replace('"', '\\"')
                commit_stdout, commit_stderr = await self._run_subprocess(f'git commit -m "{safe_msg}"', cwd)
                
                return self._result(True, f"Auto-commit successful: {safe_msg}\\n\\n{commit_stdout}", commit_stderr, f'git commit -m "{safe_msg}"')

            elif git_cmd == "auto_push":
                stdout, stderr = await self._run_subprocess("git push", cwd)
                return self._result(True, f"Pushed successfully.\\n{stdout}", stderr, "git push")

            else:
                stdout, stderr = await self._run_subprocess(f"git {git_cmd}", cwd)
                return self._result(True, stdout, stderr, f"git {git_cmd}")

        except Exception as e:
            return self._result(False, "", str(e), "")

    async def _run_subprocess(self, cmd: str, cwd: str):
        proc = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode() if stdout else "", stderr.decode() if stderr else ""

    async def _generate_llm_response(self, prompt: str, api_key: str, provider: str) -> str:
        if not api_key: return "Auto-commit: Updates applied."
        try:
            if provider == "groq":
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                data = {"model": "llama3-70b-8192", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
                return res.json()["choices"][0]["message"]["content"].strip()
            elif provider == "gemini":
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                return response.text.strip()
            else:
                return "Auto-commit: Updates applied."
        except Exception:
            return "Auto-commit: Updates applied."

    def _result(self, success: bool, stdout: str, stderr: str, cmd: str) -> Dict[str, Any]:
        return {
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "action": "GIT_AUTOMATION",
            "sysCommand": cmd
        }

    async def verify(self, execution_result: Dict[str, Any]) -> bool:
        return execution_result.get("success", False)
