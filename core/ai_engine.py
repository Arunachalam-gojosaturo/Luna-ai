"""
Luna AI Engine v5 — Gemini / Groq / Ollama
Sends system context, returns structured responses.
"""
import re
import psutil
from datetime import datetime
from pathlib import Path

SYSTEM_PROMPT = """You are Luna, an advanced AI assistant with full system access.
Capabilities: file system operations, code execution, music downloads, package installation, system monitoring.

RULES FOR RESPONSES:
1. Be concise and intelligent. 2-4 sentences of explanation max.
2. For code: ALWAYS wrap in ```language ... ``` fences. Explain BEFORE showing code.
3. For tasks (create file/dir, download, install): Confirm what you're doing, then do it.
4. Never use markdown asterisks or hash symbols in your spoken explanations.
5. When user asks to save/write code to a file, say "Saving to workspace..." before the code block.
6. Format file paths as `path/to/file` for visibility.
"""


class AIEngine:
    def __init__(self, mem):
        self.mem = mem

    @property
    def provider(self):   return self.mem.get("provider",   "gemini")
    @property
    def model(self):      return self.mem.get("model",      "gemini-2.0-flash")
    @property
    def api_key(self):    return self.mem.get("api_key",    "")
    @property
    def groq_key(self):   return self.mem.get("groq_api_key", "")
    @property
    def ollama_model(self): return self.mem.get("ollama_model", "llama3")

    def get_system_context(self) -> str:
        cpu  = psutil.cpu_percent(interval=0.1)
        ram  = psutil.virtual_memory()
        now  = datetime.now().strftime("%A %B %d %Y, %I:%M %p")
        ws   = self.mem.get("workspace_dir", str(Path.home() / "LunaWorkspace"))
        user = self.mem.get_user_name() or "User"
        return (f"[System: {now} | CPU {cpu}% | RAM {ram.percent}% | "
                f"User: {user} | Workspace: {ws}]")

    def process(self, text: str, history: list | None = None) -> str:
        t = text.lower().strip()

        # Quick built-ins
        if re.fullmatch(r"(hi|hello|hey|yo|sup)", t):
            n = self.mem.get_user_name()
            return f"Hey{' ' + n if n else ''}! What can I do for you?"

        if m := re.search(r"my name is (.+)", t):
            name = m.group(1).strip().title()
            self.mem.set_user_name(name)
            return f"Got it, I'll remember you as {name}."

        if re.search(r"^(time|what.?s the time)$", t):
            return datetime.now().strftime("It's %I:%M %p.")

        if re.search(r"^(date|what.?s the date|today)$", t):
            return datetime.now().strftime("Today is %A, %B %d, %Y.")

        if any(k in t for k in ("system status", "cpu", "ram", "memory", "system info")):
            cpu = psutil.cpu_percent(interval=0.5)
            vm  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return (f"System OK. CPU at {cpu}%, RAM {vm.percent}% "
                    f"({vm.used//1024**3:.1f}GB / {vm.total//1024**3:.1f}GB), "
                    f"Disk {disk.percent}% used.")

        if "clear" in t and ("chat" in t or "history" in t):
            self.mem.clear_history()
            return "Chat history cleared."

        if self.provider == "gemini":  return self._gemini(text, history)
        if self.provider == "groq":    return self._groq(text, history)
        if self.provider == "ollama":  return self._ollama(text)
        return "No AI provider configured. Open Settings ⚙ to add your API key."

    def _build_messages(self, text, history):
        msgs = [{"role": "user",
                 "content": SYSTEM_PROMPT + "\n" + self.get_system_context()}]
        if history:
            for h in history[-8:]:
                msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": text})
        return msgs

    def _gemini(self, text, history) -> str:
        if not self.api_key:
            return "Gemini API key is not set. Open Settings ⚙ to add it."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            ctx = [SYSTEM_PROMPT, self.get_system_context(), ""]
            if history:
                for h in history[-8:]:
                    role = "User" if h["role"] == "user" else "Luna"
                    ctx.append(f"{role}: {h['content']}")
            ctx.append(f"User: {text}\nLuna:")
            resp = client.models.generate_content(
                model=self.model, contents="\n".join(ctx))
            return resp.text.strip()
        except ImportError:
            return "google-genai not installed. Run: pip install google-genai"
        except Exception as e:
            return f"Gemini error: {str(e)[:200]}"

    def _groq(self, text, history) -> str:
        if not self.groq_key:
            return "Groq API key is not set. Open Settings ⚙ to add it."
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            msgs = [{"role": "system", "content": SYSTEM_PROMPT + "\n" + self.get_system_context()}]
            if history:
                for h in history[-8:]:
                    msgs.append({"role": h["role"], "content": h["content"]})
            msgs.append({"role": "user", "content": text})
            resp = client.chat.completions.create(
                model=self.model, messages=msgs, max_tokens=800, temperature=0.7)
            return resp.choices[0].message.content.strip()
        except ImportError:
            return "groq not installed. Run: pip install groq"
        except Exception as e:
            return f"Groq error: {str(e)[:200]}"

    def _ollama(self, text) -> str:
        try:
            import requests
            payload = {"model": self.ollama_model,
                       "prompt": f"{SYSTEM_PROMPT}\n{self.get_system_context()}\nUser: {text}\nLuna:",
                       "stream": False}
            r = requests.post("http://localhost:11434/api/generate",
                              json=payload, timeout=60)
            if r.status_code == 200:
                return r.json().get("response", "").strip()
            return f"Ollama status {r.status_code}."
        except Exception as e:
            return f"Ollama error: {str(e)[:120]}"

    @staticmethod
    def gemini_models():
        return [
            ("gemini-2.0-flash",                   "Gemini 2.0 Flash  ★"),
            ("gemini-2.0-flash-thinking-exp-01-21", "Gemini 2.0 Flash Thinking"),
            ("gemini-1.5-pro",                     "Gemini 1.5 Pro"),
            ("gemini-1.5-flash",                   "Gemini 1.5 Flash"),
        ]

    @staticmethod
    def groq_models():
        return [
            ("llama-3.3-70b-versatile",        "LLaMA 3.3 70B  ★"),
            ("llama-3.1-8b-instant",           "LLaMA 3.1 8B Instant"),
            ("mixtral-8x7b-32768",             "Mixtral 8x7B"),
            ("gemma2-9b-it",                   "Gemma 2 9B"),
            ("deepseek-r1-distill-llama-70b",  "DeepSeek R1 70B"),
        ]
