#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
[ -f "venv/bin/activate" ] && source venv/bin/activate || \
[ -f ".venv/bin/activate" ] && source .venv/bin/activate

echo "[~] Recoding Luna AI engine — full answers, web search, detailed responses..."

# ── Install requests for web search ───────────────────────────────────────────
python3 -m pip install -q requests beautifulsoup4
echo "[✓] Dependencies ready"

# ══════════════════════════════════════════════════════════
#  core/web_search.py — live data fetcher
# ══════════════════════════════════════════════════════════
cat > "$DIR/core/web_search.py" << 'PYEOF'
"""
Luna Web Search — fetches live data for prices, news, weather etc.
Called by AI engine BEFORE sending to LLM so LLM can include real data.
"""
import re, urllib.parse, json
from datetime import datetime

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


def _get(url: str, timeout=6) -> str:
    try:
        r = requests.get(url, timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0"})
        return r.text if r.status_code == 200 else ""
    except Exception:
        return ""


def get_crypto_price(coin: str) -> str:
    """Fetch live crypto price from CoinGecko (free, no API key)."""
    ids = {
        "btc": "bitcoin", "bitcoin": "bitcoin",
        "eth": "ethereum", "ethereum": "ethereum",
        "sol": "solana", "solana": "solana",
        "bnb": "binancecoin", "binance": "binancecoin",
        "xrp": "ripple", "ripple": "ripple",
        "ada": "cardano", "cardano": "cardano",
        "doge": "dogecoin", "dogecoin": "dogecoin",
        "ltc": "litecoin", "litecoin": "litecoin",
        "dot": "polkadot", "polkadot": "polkadot",
        "avax": "avalanche-2", "avalanche": "avalanche-2",
        "matic": "matic-network", "polygon": "matic-network",
        "link": "chainlink", "chainlink": "chainlink",
        "uni": "uniswap", "uniswap": "uniswap",
        "atom": "cosmos", "cosmos": "cosmos",
    }
    coin_id = ids.get(coin.lower(), coin.lower())
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
        r = requests.get(url, timeout=6)
        data = r.json()
        if coin_id in data:
            d = data[coin_id]
            price  = d.get("usd", 0)
            change = d.get("usd_24h_change", 0)
            mcap   = d.get("usd_market_cap", 0)
            arrow  = "▲" if change >= 0 else "▼"
            return (f"${price:,.2f} USD | 24h: {arrow} {abs(change):.2f}% | "
                    f"Market Cap: ${mcap/1e9:.2f}B")
    except Exception:
        pass
    return ""


def get_stock_price(symbol: str) -> str:
    """Fetch stock price from Yahoo Finance."""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?interval=1d&range=1d"
        r = requests.get(url, timeout=6,
                         headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()
        meta = data["chart"]["result"][0]["meta"]
        price  = meta.get("regularMarketPrice", 0)
        prev   = meta.get("previousClose", 0)
        change = ((price - prev) / prev * 100) if prev else 0
        arrow  = "▲" if change >= 0 else "▼"
        return f"${price:.2f} USD | Change: {arrow} {abs(change):.2f}%"
    except Exception:
        return ""


def get_weather(city: str) -> str:
    """Get weather from wttr.in (free, no API key)."""
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        r = requests.get(url, timeout=6)
        data = r.json()
        curr = data["current_condition"][0]
        temp_c   = curr["temp_C"]
        temp_f   = curr["temp_F"]
        feels_c  = curr["FeelsLikeC"]
        humidity = curr["humidity"]
        desc     = curr["weatherDesc"][0]["value"]
        wind     = curr["windspeedKmph"]
        return (f"{desc} | {temp_c}°C ({temp_f}°F) | "
                f"Feels like {feels_c}°C | Humidity {humidity}% | Wind {wind}km/h")
    except Exception:
        return ""


def detect_and_fetch(text: str) -> str:
    """
    Detect if query needs live data, fetch it, return context string for LLM.
    Returns empty string if no live data needed.
    """
    if not _HAS_REQUESTS:
        return ""

    tl = text.lower()
    extra = ""

    # Crypto price
    crypto_match = re.search(
        r"\b(bitcoin|btc|ethereum|eth|solana|sol|bnb|xrp|ripple|ada|cardano|"
        r"doge|dogecoin|ltc|litecoin|dot|polkadot|avax|avalanche|matic|polygon|"
        r"link|chainlink|uni|uniswap|atom|cosmos)\b.*?"
        r"(?:price|worth|cost|value|rate|usd|market|trading|at|is|now|today|live|current)",
        tl)
    if not crypto_match:
        crypto_match = re.search(
            r"(?:price|worth|cost|value|rate|usd|market|trading|at|is|now|today|live|current).*?"
            r"\b(bitcoin|btc|ethereum|eth|solana|sol|bnb|xrp|ada|doge|ltc|dot|avax|matic|link)\b",
            tl)

    if crypto_match:
        coin = next((g for g in crypto_match.groups() if g), "btc")
        price = get_crypto_price(coin)
        if price:
            extra += f"\n[LIVE DATA] {coin.upper()} Price: {price}\n"

    # Stock price
    stock_match = re.search(
        r"\b(aapl|apple|googl|google|msft|microsoft|amzn|amazon|tsla|tesla|"
        r"meta|nvda|nvidia|nflx|netflix|amd|intc|intel|spy|qqq|dow)\b.*?"
        r"(?:price|stock|share|worth|trading|value)",
        tl)
    if not stock_match:
        stock_match = re.search(
            r"(?:price|stock|share|worth|trading|value).*?"
            r"\b(aapl|googl|msft|amzn|tsla|meta|nvda|nflx|amd|intc|spy|qqq)\b",
            tl)

    if stock_match:
        sym = next((g for g in stock_match.groups() if g), "")
        sym_map = {"apple":"AAPL","google":"GOOGL","microsoft":"MSFT","amazon":"AMZN",
                   "tesla":"TSLA","nvidia":"NVDA","netflix":"NFLX","intel":"INTC","amd":"AMD"}
        sym = sym_map.get(sym.lower(), sym.upper())
        price = get_stock_price(sym)
        if price:
            extra += f"\n[LIVE DATA] {sym} Stock: {price}\n"

    # Weather
    weather_match = re.search(
        r"weather\s+(?:in\s+|at\s+|for\s+)?([a-zA-Z\s]+?)(?:\s+today|\s+now|\s+like|$|\?)", tl)
    if not weather_match:
        weather_match = re.search(
            r"(?:temperature|temp|climate|forecast)\s+(?:in\s+|at\s+)?([a-zA-Z\s]+?)(?:\s*$|\?)", tl)
    if weather_match:
        city = weather_match.group(1).strip()
        if city and len(city) > 1:
            w = get_weather(city)
            if w:
                extra += f"\n[LIVE DATA] Weather in {city.title()}: {w}\n"

    return extra
PYEOF
echo "[✓] core/web_search.py"

# ══════════════════════════════════════════════════════════
#  core/ai_engine.py — FULL RECODE
#  - Longer detailed answers (10-20 lines with bullet points)
#  - Live data injection (BTC, stocks, weather)
#  - NOT restricted by fake "task engine" prompt
# ══════════════════════════════════════════════════════════
cat > "$DIR/core/ai_engine.py" << 'PYEOF'
"""
Luna AI Engine v6 — Full detailed answers
- Long responses with bullet points (10-20 lines)
- Live data: crypto prices, stocks, weather
- System commands confirmed short, questions answered FULLY
"""
import re, psutil
from datetime import datetime
from pathlib import Path

try:
    from core.web_search import detect_and_fetch
    _HAS_WEBSEARCH = True
except Exception:
    _HAS_WEBSEARCH = False
    def detect_and_fetch(t): return ""


SYSTEM_PROMPT = """You are Luna, an elite AI assistant running on Arch Linux with Hyprland.
You were built to be deeply knowledgeable, sharp, and thorough.

PERSONALITY:
- Call the user "Boss" occasionally
- Speak like a brilliant hacker who knows everything
- Confident, direct, never vague

RESPONSE FORMAT RULES — CRITICAL:
1. For ANY question about facts, technology, prices, explanations, how-to, news, science, history, coding:
   - Give a DETAILED answer: minimum 10 lines
   - Use bullet points (• symbol) for lists
   - Use numbered steps for processes
   - Include examples where relevant
   - Include context, background, implications
   - Never give a one-liner for a real question

2. For system task confirmations (song playing, volume set, brightness changed):
   - Keep it SHORT: 1 sentence only
   - Just confirm what happened

3. For greetings: 2-3 lines, friendly and sharp

4. For coding questions:
   - Explain the concept first (3-5 lines)
   - Show the code with comments
   - Explain what each part does
   - Mention common pitfalls
   - Suggest improvements

5. LIVE DATA: If [LIVE DATA] appears in context, include those exact numbers in your answer.
   Never say you cannot access real-time data if live data is provided to you.

6. Never say "I cannot", "I don't have access", "as an AI" — just answer.

7. Use markdown formatting:
   • Bullet points for lists
   **bold** for important terms
   `code` for inline code
   ```language for code blocks```

TOPICS YOU EXCEL AT:
- Cryptocurrency, DeFi, blockchain, trading
- Linux, Arch, Hyprland, terminal, shell scripting
- Programming in Python, Rust, JS, C++, Bash
- System administration, networking, security
- AI/ML concepts and implementation
- Current events (if live data provided)
- Mathematics, physics, science
- Philosophy, history, culture
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
            disk = psutil.disk_usage("/")
            now  = datetime.now().strftime("%A, %B %d %Y — %I:%M %p")
            user = self.mem.get_user_name() or "Boss"
            return (
                f"[SYSTEM CONTEXT]\n"
                f"Date/Time: {now}\n"
                f"OS: Arch Linux + Hyprland (Wayland)\n"
                f"CPU Usage: {cpu:.1f}% | RAM: {ram.percent:.1f}% "
                f"({ram.used//1024**3:.1f}/{ram.total//1024**3:.1f} GB) | "
                f"Disk: {disk.percent:.1f}%\n"
                f"Operator: {user}\n"
            )
        except Exception:
            return "[SYSTEM: Arch Linux + Hyprland]"

    def _quick_replies(self, text: str, tl: str):
        """Handle simple built-in commands without calling LLM."""
        if re.fullmatch(r"(hi|hello|hey|yo|sup|hiya|hola)", tl):
            n = self.mem.get_user_name() or "Boss"
            return (
                f"Hey {n}! Luna is fully online and ready.\n"
                "All systems nominal — task engine armed, voice active.\n"
                "What do you need? Ask me anything."
            )

        if m := re.search(r"my name is (.+)", tl):
            name = m.group(1).strip().title()
            self.mem.set_user_name(name)
            return (
                f"Identity registered: **{name}**.\n"
                f"Welcome, {name}. I'll address you by name from now on.\n"
                "You can change it anytime by saying 'my name is ...' again."
            )

        if re.fullmatch(r"(time|what.?s the time|current time|what time is it)", tl):
            return f"Current time: **{datetime.now().strftime('%I:%M:%S %p')}**"

        if re.fullmatch(r"(date|today|what.?s the date|current date|what day is it)", tl):
            return f"Today is **{datetime.now().strftime('%A, %B %d, %Y')}**"

        if "clear" in tl and ("chat" in tl or "history" in tl):
            self.mem.clear_history()
            return "Chat history cleared. Fresh start, Boss."

        return None

    def process(self, text: str, history=None) -> str:
        tl = text.lower().strip()

        # Quick built-in replies
        quick = self._quick_replies(text, tl)
        if quick:
            return quick

        # Fetch live data if needed (crypto, stocks, weather)
        live_data = ""
        if _HAS_WEBSEARCH:
            try:
                live_data = detect_and_fetch(text)
            except Exception:
                live_data = ""

        # Build full prompt with live data injected
        augmented_text = text
        if live_data:
            augmented_text = f"{text}\n{live_data}"

        if self.provider == "gemini":  return self._gemini(augmented_text, history)
        if self.provider == "groq":    return self._groq(augmented_text, history)
        if self.provider == "ollama":  return self._ollama(augmented_text)
        return (
            "**No AI provider configured.**\n"
            "Go to Settings ⚙ and add your API key.\n\n"
            "Supported providers:\n"
            "• **Gemini** — Get free key at aistudio.google.com\n"
            "• **Groq** — Get free key at console.groq.com\n"
            "• **Ollama** — Run locally, install from ollama.ai"
        )

    def _build_history(self, history, limit=12):
        msgs = []
        if history:
            for h in history[-limit:]:
                msgs.append({
                    "role": h["role"],
                    "content": h["content"]
                })
        return msgs

    def _gemini(self, text: str, history) -> str:
        if not self.api_key:
            return (
                "**Gemini API key not set.**\n"
                "1. Go to aistudio.google.com\n"
                "2. Create a free API key\n"
                "3. Open Luna Settings ⚙ and paste it in"
            )
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)

            # Build conversation
            parts = [SYSTEM_PROMPT, "\n", self._ctx(), "\n"]

            if history:
                for h in history[-12:]:
                    role = "Boss" if h["role"] == "user" else "Luna"
                    parts.append(f"{role}: {h['content']}")

            parts.append(f"\nBoss: {text}")
            parts.append("\nLuna (give a thorough, detailed answer with bullet points if listing things — minimum 10 lines for questions):")

            prompt = "\n".join(parts)

            resp = client.models.generate_content(
                model=self.model,
                contents=prompt)
            return resp.text.strip()

        except ImportError:
            return "google-genai not installed. Run: pip install google-genai"
        except Exception as e:
            err = str(e)
            if "API_KEY_INVALID" in err or "API key" in err.lower():
                return "Invalid Gemini API key. Check Settings ⚙."
            if "quota" in err.lower() or "429" in err:
                return "Gemini quota exceeded. Try again in a minute or switch to Groq."
            return f"Gemini error: {err[:300]}"

    def _groq(self, text: str, history) -> str:
        if not self.groq_key:
            return (
                "**Groq API key not set.**\n"
                "1. Go to console.groq.com\n"
                "2. Create a free API key\n"
                "3. Open Luna Settings ⚙ and paste it in"
            )
        try:
            from groq import Groq

            client = Groq(api_key=self.groq_key)
            messages = [{"role": "system",
                         "content": SYSTEM_PROMPT + "\n" + self._ctx()}]

            if history:
                for h in history[-12:]:
                    messages.append({
                        "role": h["role"],
                        "content": h["content"]
                    })

            messages.append({"role": "user", "content": text})

            resp = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2048,
                temperature=0.7)
            return resp.choices[0].message.content.strip()

        except ImportError:
            return "groq not installed. Run: pip install groq"
        except Exception as e:
            err = str(e)
            if "401" in err or "api_key" in err.lower():
                return "Invalid Groq API key. Check Settings ⚙."
            if "429" in err or "rate" in err.lower():
                return "Groq rate limit hit. Wait a moment then try again."
            return f"Groq error: {err[:300]}"

    def _ollama(self, text: str) -> str:
        try:
            import requests
            payload = {
                "model": self.ollama_model,
                "prompt": (
                    SYSTEM_PROMPT + "\n" +
                    self._ctx() + "\n" +
                    f"Boss: {text}\n"
                    "Luna (give detailed answer, minimum 10 lines, use bullet points):"
                ),
                "stream": False,
            }
            r = requests.post("http://localhost:11434/api/generate",
                              json=payload, timeout=90)
            if r.status_code == 200:
                return r.json().get("response", "").strip()
            return f"Ollama returned status {r.status_code}."
        except requests.exceptions.ConnectionError:
            return (
                "**Ollama not running.**\n"
                "Start it with: `ollama serve`\n"
                "Then pull a model: `ollama pull llama3`"
            )
        except Exception as e:
            return f"Ollama error: {str(e)[:200]}"

    @staticmethod
    def gemini_models():
        return [
            ("gemini-2.0-flash",                    "Gemini 2.0 Flash  ★ Recommended"),
            ("gemini-2.0-flash-thinking-exp-01-21", "Gemini 2.0 Flash Thinking"),
            ("gemini-1.5-pro",                      "Gemini 1.5 Pro"),
            ("gemini-1.5-flash",                    "Gemini 1.5 Flash"),
            ("gemini-2.0-pro-exp",                  "Gemini 2.0 Pro (Experimental)"),
        ]

    @staticmethod
    def groq_models():
        return [
            ("llama-3.3-70b-versatile",       "LLaMA 3.3 70B  ★ Recommended"),
            ("llama-3.1-8b-instant",          "LLaMA 3.1 8B  (Fast)"),
            ("mixtral-8x7b-32768",            "Mixtral 8x7B"),
            ("gemma2-9b-it",                  "Gemma 2 9B"),
            ("deepseek-r1-distill-llama-70b", "DeepSeek R1 70B  (Reasoning)"),
            ("llama3-70b-8192",               "LLaMA 3 70B"),
        ]
PYEOF
echo "[✓] core/ai_engine.py"

# ══════════════════════════════════════════════════════════
#  Fix greet() — proper multiline without f-string bug
# ══════════════════════════════════════════════════════════
echo "[~] Fixing greet() welcome message..."
python3 - << 'PYEOF'
import re

path = "ui/main_window.py"
with open(path) as f:
    src = f.read()

new_greet = '''    def greet(self):
        user = self.mem.get_user_name()
        if user:
            msg = (
                "[LUNA v5] SYSTEM ONLINE" + "\\n" +
                "Operator: " + user + " | Arch Linux + Hyprland | Status: NOMINAL" + "\\n" +
                "Neural core initialized. Voice engine active. Task engine armed." + "\\n" +
                "Live data feeds connected. Firefox controller ready." + "\\n" +
                "Say my name to wake me, Boss. What is the move?"
            )
        else:
            msg = (
                "[LUNA v5] SYSTEM ONLINE" + "\\n" +
                "Arch Linux + Hyprland | All modules initialized." + "\\n" +
                "No operator profile detected. Open Settings to add your API key." + "\\n" +
                "Say your name: type  my name is YourName  to register." + "\\n" +
                "Say Luna anytime to activate voice mode. Awaiting orders, Boss."
            )
        self._add(msg, "ai")
        self.set_status("SPEAKING")
        if self._wake:
            self._wake.pause()
        speak_msg = ("Luna online. Welcome back " + user + ". What is the move?") if user else "Luna online. Awaiting orders, Boss."
        self.voice.speak_async(
            speak_msg,
            on_done=lambda: (
                self.set_status("READY"),
                self._wake.resume() if self._wake else None
            )
        )
'''

# Replace entire greet method
result = re.sub(
    r'(\n    def greet\(self\):).*?(\n    def [a-z]|\nclass |\Z)',
    lambda m: new_greet + (m.group(2) if m.group(2).strip() else ""),
    src,
    flags=re.DOTALL
)

if result == src:
    # Fallback: line-by-line replace
    lines = src.split("\n")
    out = []
    in_greet = False
    depth = 0
    for line in lines:
        if "def greet(self):" in line and line.startswith("    def"):
            in_greet = True
            depth = 0
            for nl in new_greet.rstrip("\n").split("\n"):
                out.append(nl)
            continue
        if in_greet:
            stripped = line.strip()
            if stripped.startswith("def ") and not stripped.startswith("def greet"):
                in_greet = False
                out.append(line)
            continue
        out.append(line)
    result = "\n".join(out)

with open(path, "w") as f:
    f.write(result)

# Verify syntax
import ast
try:
    ast.parse(result)
    print("  [✓] greet() fixed, syntax OK")
except SyntaxError as e:
    print(f"  [!] Syntax error at line {e.lineno}: {e.msg}")
PYEOF

echo ""
echo "  ╔════════════════════════════════════════════════╗"
echo "  ║  LUNA AI v6 — FULL RECODE DONE              ║"
echo "  ╠════════════════════════════════════════════════╣"
echo "  ║  What changed:                              ║"
echo "  ║  • Answers are now 10-20 lines with bullets ║"
echo "  ║  • BTC/ETH/crypto prices: LIVE via CoinGecko║"
echo "  ║  • Stock prices: LIVE via Yahoo Finance     ║"
echo "  ║  • Weather: LIVE via wttr.in               ║"
echo "  ║  • No more 'Done' for real questions       ║"
echo "  ║  • History kept for context (12 messages)  ║"
echo "  ╠════════════════════════════════════════════════╣"
echo "  ║  Test these:                                ║"
echo "  ║   what is the price of bitcoin             ║"
echo "  ║   what is ethereum worth                   ║"
echo "  ║   weather in Mumbai                         ║"
echo "  ║   explain quantum computing                 ║"
echo "  ║   how does blockchain work                  ║"
echo "  ║   write me a python web scraper             ║"
echo "  ╚════════════════════════════════════════════════╝"
echo ""
echo "  Run: python main.py"
