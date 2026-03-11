import json
from pathlib import Path

DEFAULTS = {
    "user_name": "",
    "provider": "gemini",
    "model": "gemini-2.0-flash",
    "api_key": "",
    "groq_api_key": "",
    "ollama_model": "llama3",
    "voice": "en-US-AriaNeural",
    "voice_rate": "-5%",
    "voice_pitch": "+0Hz",
    "download_dir": str(Path.home() / "Music"),
    "workspace_dir": str(Path.home() / "LunaWorkspace"),
    "chat_history": [],
    "allow_system_commands": True,
}

class MemoryManager:
    def __init__(self):
        self.dir = Path.home() / ".luna_ai"
        self.dir.mkdir(exist_ok=True)
        self.file = self.dir / "config.json"
        self.data = {}
        self._load()
        # Ensure workspace dir exists
        Path(self.data.get("workspace_dir", DEFAULTS["workspace_dir"])).mkdir(parents=True, exist_ok=True)

    def _load(self):
        if self.file.exists():
            try:
                self.data = json.loads(self.file.read_text())
            except Exception:
                self.data = {}
        for k, v in DEFAULTS.items():
            if k not in self.data:
                self.data[k] = v

    def save(self):
        self.file.write_text(json.dumps(self.data, indent=2))

    def get(self, key, default=None):
        return self.data.get(key, DEFAULTS.get(key, default))

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def get_user_name(self):
        return self.data.get("user_name", "")

    def set_user_name(self, name):
        self.set("user_name", name)

    def update_settings(self, d: dict):
        for k, v in d.items():
            self.data[k] = v
        self.save()

    def add_to_history(self, role: str, content: str):
        h = self.data.get("chat_history", [])
        h.append({"role": role, "content": content})
        self.data["chat_history"] = h[-30:]
        self.save()

    def get_history(self):
        return self.data.get("chat_history", [])

    def clear_history(self):
        self.data["chat_history"] = []
        self.save()
