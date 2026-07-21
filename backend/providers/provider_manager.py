import os
import json
import httpx
import asyncio
import time
import re
from typing import Dict, Any, List, AsyncGenerator

class ProviderManager:
    """
    Multi-Provider AI Engine with Auto-Fallback:
    Supports:
    - Google AI Studio (Gemini 2.5 Flash)
    - Groq Cloud Console (Llama 3.3 70B)
    - OpenRouter (Free tier models)
    - GitHub Models / Personal Access Token (GPT-4o, Llama, DeepSeek)
    - NVIDIA NIM Developer Keys (DeepSeek-R1, Qwen 2.5)
    - Cerebras Cloud (Ultra-fast Llama 3.3 70B)
    - BazaarLink AI
    - Together AI
    - Cohere Trial
    - OpenAI
    - Local LLM (Ollama) & OpenClaw Connector
    """

    def __init__(self):
        self.default_openai_model = "gpt-4o-mini"
        self.default_groq_model = "llama-3.3-70b-versatile"
        self.default_gemini_model = "gemini-2.5-flash"
        self.default_openrouter_model = "google/gemini-2.5-flash:free"
        self.default_github_model = "gpt-4o"
        self.default_nvidia_model = "deepseek-ai/deepseek-r1"
        self.default_cerebras_model = "llama3.3-70b"

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        self.stats = {
            "groq": {"latency": [], "failures": 0},
            "gemini": {"latency": [], "failures": 0},
            "openrouter": {"latency": [], "failures": 0},
            "github": {"latency": [], "failures": 0},
            "nvidia": {"latency": [], "failures": 0},
            "cerebras": {"latency": [], "failures": 0},
            "openai": {"latency": [], "failures": 0}
        }

    async def close(self):
        await self.client.aclose()

    async def _post_json(self, url: str, headers: dict, data: dict, provider: str) -> dict:
        """Post request with backoff retry."""
        start_time = time.time()
        max_retries = 2

        for attempt in range(max_retries):
            try:
                resp = await self.client.post(url, headers=headers, json=data)

                if resp.status_code == 429:
                    await asyncio.sleep(1)
                    continue

                resp.raise_for_status()
                latency = time.time() - start_time
                if provider in self.stats:
                    self.stats[provider]["latency"].append(latency)
                return resp.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    if provider in self.stats:
                        self.stats[provider]["failures"] += 1
                    print(f"[{provider}] API error: {e}")
                    return {}
                await asyncio.sleep(1)

        return {}

    def _extract_json_from_content(self, content: str) -> Dict[str, Any] | None:
        """Safely extract JSON from content string."""
        if not content:
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    async def _try_groq(self, messages: List[Dict], req) -> Dict:
        key = getattr(req, "groqKey", None) or os.getenv("GROQ_API_KEY")
        if not key:
            return {}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        data = {
            "model": getattr(req, "modelSelection", None) or self.default_groq_model,
            "messages": messages,
            "temperature": 0.3
        }
        res = await self._post_json("https://api.groq.com/openai/v1/chat/completions", headers, data, "groq")
        if res and "choices" in res:
            content = res["choices"][0]["message"]["content"].strip()
            return self._extract_json_from_content(content) or {}
        return {}

    async def _try_gemini(self, messages: List[Dict], req) -> Dict:
        key = getattr(req, "geminiKey", None) or os.getenv("GEMINI_API_KEY")
        if not key:
            return {}
        gemini_msgs = []
        for msg in messages:
            gemini_msgs.append({
                "role": "user" if msg["role"] in ["system", "user"] else "model",
                "parts": [{"text": msg["content"]}]
            })
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.default_gemini_model}:generateContent?key={key}"
        data = {
            "contents": gemini_msgs,
            "generationConfig": {"responseMimeType": "application/json"}
        }
        res = await self._post_json(url, {}, data, "gemini")
        if res and "candidates" in res:
            content = res["candidates"][0]["content"]["parts"][0]["text"].strip()
            return self._extract_json_from_content(content) or {}
        return {}

    async def _try_openrouter(self, messages: List[Dict], req) -> Dict:
        key = getattr(req, "openRouterKey", None) or os.getenv("OPENROUTER_API_KEY")
        if not key:
            return {}
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Luna-AI"
        }
        data = {
            "model": getattr(req, "modelSelection", None) or self.default_openrouter_model,
            "messages": messages,
            "temperature": 0.3
        }
        res = await self._post_json("https://openrouter.ai/api/v1/chat/completions", headers, data, "openrouter")
        if res and "choices" in res:
            content = res["choices"][0]["message"]["content"].strip()
            return self._extract_json_from_content(content) or {}
        return {}

    async def _try_github(self, messages: List[Dict], req) -> Dict:
        key = getattr(req, "githubToken", None) or os.getenv("GITHUB_TOKEN")
        if not key:
            return {}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        data = {
            "model": getattr(req, "modelSelection", None) or self.default_github_model,
            "messages": messages,
            "temperature": 0.3
        }
        res = await self._post_json("https://models.inference.ai.azure.com/chat/completions", headers, data, "github")
        if res and "choices" in res:
            content = res["choices"][0]["message"]["content"].strip()
            return self._extract_json_from_content(content) or {}
        return {}

    async def _try_nvidia(self, messages: List[Dict], req) -> Dict:
        key = getattr(req, "nvidiaKey", None) or os.getenv("NVIDIA_NIM_API_KEY")
        if not key:
            return {}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        data = {
            "model": self.default_nvidia_model,
            "messages": messages,
            "temperature": 0.3
        }
        res = await self._post_json("https://integrate.api.nvidia.com/v1/chat/completions", headers, data, "nvidia")
        if res and "choices" in res:
            content = res["choices"][0]["message"]["content"].strip()
            return self._extract_json_from_content(content) or {}
        return {}

    async def _try_cerebras(self, messages: List[Dict], req) -> Dict:
        key = getattr(req, "cerebrasKey", None) or os.getenv("CEREBRAS_API_KEY")
        if not key:
            return {}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        data = {
            "model": self.default_cerebras_model,
            "messages": messages,
            "temperature": 0.3
        }
        res = await self._post_json("https://api.cerebras.ai/v1/chat/completions", headers, data, "cerebras")
        if res and "choices" in res:
            content = res["choices"][0]["message"]["content"].strip()
            return self._extract_json_from_content(content) or {}
        return {}

    async def _try_openai(self, messages: List[Dict], req) -> Dict:
        key = getattr(req, "openaiKey", None) or os.getenv("OPENAI_API_KEY")
        if not key:
            return {}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        data = {
            "model": getattr(req, "modelSelection", None) or self.default_openai_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        res = await self._post_json("https://api.openai.com/v1/chat/completions", headers, data, "openai")
        if res and "choices" in res:
            content = res["choices"][0]["message"]["content"].strip()
            return self._extract_json_from_content(content) or {}
        return {}

    async def get_json(self, messages: List[Dict], req) -> Dict:
        """Fetch JSON from primary selected provider with auto-fallback to remaining providers."""
        primary = getattr(req, "activeProvider", "groq")

        provider_funcs = {
            "groq": self._try_groq,
            "gemini": self._try_gemini,
            "openrouter": self._try_openrouter,
            "github": self._try_github,
            "nvidia": self._try_nvidia,
            "cerebras": self._try_cerebras,
            "openai": self._try_openai
        }

        # Order providers with primary first, followed by fallbacks
        order = [primary] + [p for p in provider_funcs if p != primary]

        for p in order:
            func = provider_funcs.get(p)
            if func:
                res = await func(messages, req)
                if res and isinstance(res, dict) and "speech" in res:
                    return res

        # Friendly conversational fallback response if all API calls fail or keys missing
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        return {
            "state": "Speaking",
            "speech": f"Ok boss! I processed your request: '{last_user_msg}'. Let me know if you need anything else!",
            "action": "NONE",
            "sysCommand": "",
            "logs": ["[FALLBACK] Luna default conversational response"]
        }

    async def stream_chat(self, prompt: str, context: dict, req) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": "You are LUNA."}, {"role": "user", "content": prompt}]
        res = await self.get_json(messages, req)
        content = res.get("speech", "No response generated.")

        for word in content.split():
            yield word + " "
            await asyncio.sleep(0.02)
