"""Luna AI Engine — NEVER fakes system tasks"""
import re, psutil
from datetime import datetime
from pathlib import Path

# The AI will NEVER see "play", "volume", "brightness" commands
# because task_engine intercepts them first.
# This prompt is a last line of defense.
SYSTEM_PROMPT = """You are Luna, an AI assistant on Arch Linux + Hyprland.

HARD RULES — BREAKING THESE IS NOT ALLOWED:
1. You have NO ability to play music, open browsers, control volume, or change brightness.
   A hardware task engine handles those before you are called.
   If the user asked you to do a system action, it ALREADY HAPPENED.
   Say only: "Done." or confirm the action in 1 short sentence.
2. FORBIDDEN PHRASES — never say these:
   - "I'll play..."  "I will play..."  "Starting playback..."
   - "I'll open Firefox..."  "Opening YouTube..."
   - "I'll download..."  "Downloading..."
   - "I'll set the volume..."  "Adjusting volume..."
   - "I'll change brightness..."
   - "I accessed the music library"
   - "Playing in the background"
3. Keep all replies SHORT: 1-3 sentences max.
4. For code: wrap in ```language\n...\n``` fences.
5. Plain text only in speech — no **, *, or # markdown.
6. You are on Arch Linux. Use pacman/yay, wpctl, brightnessctl, hyprctl.
"""


class AIEngine:
    def __init__(self, mem):
        self.mem = mem

    @property
    def provider(self):     return self.mem.get("provider",     "gemini")
    @property
    def model(self):        return self.mem.get("model",        "gemini-2.0-flash")
    @property
    def api_key(self):      return self.mem.get("api_key",      "")
    @property
    def groq_key(self):     return self.mem.get("groq_api_key", "")
    @property
    def ollama_model(self): return self.mem.get("ollama_model", "llama3")

    def _ctx(self):
        try:
            cpu  = psutil.cpu_percent(interval=0.1)
            ram  = psutil.virtual_memory()
            now  = datetime.now().strftime("%A %B %d %Y, %I:%M %p")
            user = self.mem.get_user_name() or "User"
            return (f"[Arch+Hyprland | {now} | CPU {cpu:.0f}% | "
                    f"RAM {ram.percent:.0f}% | User:{user}]")
        except Exception:
            return "[Arch Linux + Hyprland]"

    def process(self, text:str, history=None) -> str:
        tl = text.lower().strip()
        if re.fullmatch(r"(hi|hello|hey|yo|sup|hiya)", tl):
            n = self.mem.get_user_name()
            return f"Hey{' '+n if n else ''}! What do you need?"
        if m := re.search(r"my name is (.+)", tl):
            name = m.group(1).strip().title()
            self.mem.set_user_name(name)
            return f"Got it, I'll remember you as {name}."
        if re.fullmatch(r"(time|what.?s the time|current time)", tl):
            return datetime.now().strftime("It's %I:%M %p.")
        if re.fullmatch(r"(date|today|what.?s the date|current date)", tl):
            return datetime.now().strftime("Today is %A, %B %d, %Y.")
        if "clear" in tl and ("chat" in tl or "history" in tl):
            self.mem.clear_history(); return "Chat cleared."

        if self.provider == "gemini":  return self._gemini(text, history)
        if self.provider == "groq":    return self._groq(text, history)
        if self.provider == "ollama":  return self._ollama(text)
        return "No AI provider set. Open Settings ⚙."

    def _gemini(self, text, history):
        if not self.api_key: return "Gemini API key not set. Open Settings ⚙."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            ctx = [SYSTEM_PROMPT, self._ctx(), ""]
            if history:
                for h in history[-10:]:
                    ctx.append(f"{'User' if h['role']=='user' else 'Luna'}: {h['content']}")
            ctx.append(f"User: {text}\nLuna:")
            r = client.models.generate_content(model=self.model, contents="\n".join(ctx))
            return r.text.strip()
        except ImportError: return "Install: pip install google-genai"
        except Exception as e: return f"Gemini error: {str(e)[:200]}"

    def _groq(self, text, history):
        if not self.groq_key: return "Groq API key not set. Open Settings ⚙."
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            msgs = [{"role":"system","content":SYSTEM_PROMPT+"\n"+self._ctx()}]
            if history:
                for h in history[-10:]:
                    msgs.append({"role":h["role"],"content":h["content"]})
            msgs.append({"role":"user","content":text})
            r = client.chat.completions.create(
                model=self.model, messages=msgs, max_tokens=800, temperature=0.6)
            return r.choices[0].message.content.strip()
        except ImportError: return "Install: pip install groq"
        except Exception as e: return f"Groq error: {str(e)[:200]}"

    def _ollama(self, text):
        try:
            import requests
            r = requests.post("http://localhost:11434/api/generate",
                json={"model":self.ollama_model,
                      "prompt":f"{SYSTEM_PROMPT}\n{self._ctx()}\nUser:{text}\nLuna:",
                      "stream":False}, timeout=60)
            return r.json().get("response","").strip() if r.ok else f"Ollama {r.status_code}"
        except Exception as e: return f"Ollama error: {str(e)[:120]}"

    @staticmethod
    def gemini_models():
        return [("gemini-2.0-flash","Gemini 2.0 Flash ★"),
                ("gemini-2.0-flash-thinking-exp-01-21","Gemini 2.0 Flash Thinking"),
                ("gemini-1.5-pro","Gemini 1.5 Pro"),
                ("gemini-1.5-flash","Gemini 1.5 Flash")]

    @staticmethod
    def groq_models():
        return [("llama-3.3-70b-versatile","LLaMA 3.3 70B ★"),
                ("llama-3.1-8b-instant","LLaMA 3.1 8B"),
                ("mixtral-8x7b-32768","Mixtral 8x7B"),
                ("gemma2-9b-it","Gemma 2 9B"),
                ("deepseek-r1-distill-llama-70b","DeepSeek R1 70B")]
