"""Luna AI Engine v6 — detailed answers, live data, no fake short replies."""
import re, psutil
from datetime import datetime
from pathlib import Path

try:
    from core.web_search import detect_and_fetch
    _LIVE = True
except Exception:
    _LIVE = False
    def detect_and_fetch(t): return ""

SYSTEM_PROMPT = """You are Luna, an elite AI assistant on Arch Linux with Hyprland.

PERSONALITY:
- Call the user "Boss" naturally in responses
- Sharp, knowledgeable, like a brilliant hacker
- Confident, never vague, never apologetic

RESPONSE LENGTH RULES — STRICTLY FOLLOW:
1. Questions about facts, tech, crypto, science, history, coding, explanations:
   → Give DETAILED answer: 10 to 20 lines minimum
   → Use bullet points (•) for lists
   → Use numbered steps for how-to guides
   → Include background context, real examples, implications
   → NEVER give one-liner answers to real questions

2. System confirmations (song playing, volume changed, brightness set, file created):
   → 1 short sentence only to confirm

3. Greetings: 2-3 friendly lines

4. Coding questions:
   → Explain concept (3-5 lines)
   → Provide complete working code
   → Explain key parts
   → Mention pitfalls and improvements

LIVE DATA RULE:
If [LIVE] data is in the context, use those EXACT numbers in your answer.
Never say you cannot access real-time data when live data is provided.

FORMATTING:
• Use bullet points for lists
• **bold** for key terms
• `inline code` for commands/code snippets
• Triple backtick code blocks for full code

NEVER say: "I cannot", "I don't have access", "as an AI I cannot", "I'm just an AI"
You know everything. Just answer.
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

    def _ctx(self) -> str:
        try:
            cpu  = psutil.cpu_percent(interval=0.1)
            ram  = psutil.virtual_memory()
            now  = datetime.now().strftime("%A, %B %d %Y — %I:%M %p")
            user = self.mem.get_user_name() or "Boss"
            return (f"[CONTEXT] Date: {now} | OS: Arch Linux + Hyprland | "
                    f"CPU: {cpu:.0f}% | RAM: {ram.percent:.0f}% | Operator: {user}")
        except Exception:
            return "[CONTEXT: Arch Linux + Hyprland]"

    def _quick(self, tl: str, text: str):
        if re.fullmatch(r"(hi|hello|hey|yo|sup|hiya|hola)", tl):
            n = self.mem.get_user_name() or "Boss"
            return f"Hey {n}! Luna is fully online and armed.\nAll systems nominal. What do you need?"
        if m := re.search(r"my name is (.+)", tl):
            name = m.group(1).strip().title()
            self.mem.set_user_name(name)
            return f"Identity registered: **{name}**.\nI'll address you as {name} from now on, Boss."
        if re.fullmatch(r"(time|what.?s the time|current time|what time is it)", tl):
            return f"Current time: **{datetime.now().strftime('%I:%M:%S %p')}**"
        if re.fullmatch(r"(date|today|what.?s the date|what day is it)", tl):
            return f"Today: **{datetime.now().strftime('%A, %B %d, %Y')}**"
        if "clear" in tl and ("chat" in tl or "history" in tl):
            self.mem.clear_history(); return "Chat cleared. Fresh start, Boss."
        return None

    def process(self, text: str, history=None) -> str:
        tl = text.lower().strip()
        q = self._quick(tl, text)
        if q: return q
        live = detect_and_fetch(text) if _LIVE else ""
        prompt = text + ("\n" + live if live else "")
        if self.provider == "gemini":  return self._gemini(prompt, history)
        if self.provider == "groq":    return self._groq(prompt, history)
        if self.provider == "ollama":  return self._ollama(prompt)
        return ("**No AI provider configured.**\n"
                "Open Settings ⚙ and add your API key.\n\n"
                "• **Gemini** (free): aistudio.google.com\n"
                "• **Groq** (free, fast): console.groq.com\n"
                "• **Ollama** (local): ollama.ai")

    def _gemini(self, text: str, history) -> str:
        if not self.api_key:
            return ("**Gemini API key not set.**\n"
                    "1. Visit aistudio.google.com\n"
                    "2. Sign in and create a free API key\n"
                    "3. Open Luna Settings ⚙ and paste it in the Gemini API Key field\n"
                    "4. Select Gemini as your provider and click Save")
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            parts = [SYSTEM_PROMPT, self._ctx(), ""]
            if history:
                for h in history[-14:]:
                    r = "Boss" if h["role"] == "user" else "Luna"
                    parts.append(f"{r}: {h['content']}")
            parts.append(f"\nBoss: {text}")
            parts.append("\nLuna (detailed answer, 10-20 lines for questions, bullet points for lists):")
            resp = client.models.generate_content(model=self.model, contents="\n".join(parts))
            return resp.text.strip()
        except ImportError:
            return "Install google-genai: `pip install google-genai`"
        except Exception as e:
            err = str(e)
            if "API_KEY" in err or "api key" in err.lower():
                return "Invalid Gemini API key. Check Settings ⚙."
            if "429" in err or "quota" in err.lower():
                return "Gemini quota exceeded. Wait a minute or switch to Groq in Settings."
            return f"Gemini error: {err[:300]}"

    def _groq(self, text: str, history) -> str:
        if not self.groq_key:
            return ("**Groq API key not set.**\n"
                    "1. Visit console.groq.com\n"
                    "2. Sign in and create a free API key\n"
                    "3. Open Luna Settings ⚙ and paste it in the Groq API Key field\n"
                    "4. Select Groq as your provider and click Save")
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            msgs = [{"role":"system","content":SYSTEM_PROMPT+"\n"+self._ctx()}]
            if history:
                for h in history[-14:]:
                    msgs.append({"role":h["role"],"content":h["content"]})
            msgs.append({"role":"user","content":text})
            resp = client.chat.completions.create(
                model=self.model, messages=msgs, max_tokens=2048, temperature=0.7)
            return resp.choices[0].message.content.strip()
        except ImportError:
            return "Install groq: `pip install groq`"
        except Exception as e:
            err = str(e)
            if "401" in err or "api_key" in err.lower(): return "Invalid Groq API key. Check Settings ⚙."
            if "429" in err or "rate" in err.lower(): return "Groq rate limit. Wait a moment then retry."
            return f"Groq error: {err[:300]}"

    def _ollama(self, text: str) -> str:
        try:
            import requests
            r = requests.post("http://localhost:11434/api/generate",
                json={"model":self.ollama_model,
                      "prompt":SYSTEM_PROMPT+"\n"+self._ctx()+f"\nBoss: {text}\nLuna (detailed, 10+ lines):",
                      "stream":False}, timeout=90)
            return r.json().get("response","").strip() if r.ok else f"Ollama error: {r.status_code}"
        except Exception as e:
            return ("**Ollama not running.**\n"
                    "Start it: `ollama serve`\n"
                    "Pull a model: `ollama pull llama3`")

    @staticmethod
    def gemini_models():
        return [("gemini-2.0-flash","Gemini 2.0 Flash ★"),
                ("gemini-2.0-flash-thinking-exp-01-21","Gemini 2.0 Flash Thinking"),
                ("gemini-1.5-pro","Gemini 1.5 Pro"),
                ("gemini-2.0-pro-exp","Gemini 2.0 Pro (Exp)")]

    @staticmethod
    def groq_models():
        return [("llama-3.3-70b-versatile","LLaMA 3.3 70B ★"),
                ("llama-3.1-8b-instant","LLaMA 3.1 8B Fast"),
                ("mixtral-8x7b-32768","Mixtral 8x7B"),
                ("deepseek-r1-distill-llama-70b","DeepSeek R1 70B"),
                ("gemma2-9b-it","Gemma 2 9B")]
