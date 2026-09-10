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
        self.default_gemini_model = "gemini-3.5-flash"
        self.default_openrouter_model = "google/gemini-2.0-flash-001"
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

        system_prompt = None
        gemini_contents = []
        from google.genai import types

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system" and not system_prompt:
                system_prompt = content
            else:
                gemini_role = "user" if role in ["user", "system"] else "model"
                gemini_contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content)]
                    )
                )

        if not gemini_contents and system_prompt:
            gemini_contents.append(types.Content(role="user", parts=[types.Part.from_text(text="Hello")]))

        candidate_models = []
        user_override = getattr(req, "modelSelection", None)
        if user_override:
            uo_lower = user_override.lower()
            if "3.5" in uo_lower:
                candidate_models.append("gemini-3.5-flash")
            elif "3.6" in uo_lower:
                candidate_models.append("gemini-3.6-flash")
            elif "3.8" in uo_lower:
                candidate_models.append("gemini-3.8-flash")
            elif "3.7" in uo_lower:
                candidate_models.append("gemini-3.7-flash")
            elif "gemini" in uo_lower:
                candidate_models.append(user_override)
        # Always fallback to the fastest, most reliable models first
        candidate_models.extend(["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.8-flash", "gemini-3.7-flash"])

        seen = set()
        candidate_models = [m for m in candidate_models if not (m in seen or seen.add(m))]

        try:
            from google import genai
            client = genai.Client(api_key=key)

            config_args = {
                "response_mime_type": "application/json",
                "temperature": 0.5
            }
            if system_prompt:
                config_args["system_instruction"] = system_prompt

            config = types.GenerateContentConfig(**config_args)

            for model_name in candidate_models:
                try:
                    # Timeout per candidate model to prevent stalling when high demand occurs
                    res = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.models.generate_content,
                            model=model_name,
                            contents=gemini_contents,
                            config=config
                        ),
                        timeout=5.0
                    )
                    if res and res.text:
                        parsed = self._extract_json_from_content(res.text.strip())
                        if parsed and isinstance(parsed, dict) and "speech" in parsed:
                            return parsed
                except Exception as model_err:
                    print(f"[Gemini] Model '{model_name}' failed or busy: {model_err}")
                    continue
        except Exception as e:
            print(f"[Gemini] Client error: {e}")

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
    async def _try_ollama(self, messages: List[Dict], req) -> Dict:
        """Query local Ollama instance (Offline LLM support)."""
        base_url = getattr(req, "localLlmUrl", None) or os.getenv("OLLAMA_URL", "http://localhost:11434")
        model = getattr(req, "localLlmModel", None) or os.getenv("OLLAMA_MODEL", "luna-2.5b:latest")
        
        system_prompt = ""
        user_content = ""
        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system" and not system_prompt:
                system_prompt = content
            else:
                formatted_messages.append({"role": role, "content": content})
                if role == "user":
                    user_content = content
        
        try:
            # 1. Try chat endpoint with JSON format
            chat_data = {
                "model": model,
                "messages": ([{"role": "system", "content": system_prompt}] if system_prompt else []) + formatted_messages,
                "stream": False,
                "format": "json"
            }
            res = await self.client.post(f"{base_url.rstrip('/')}/api/chat", json=chat_data, timeout=12.0)
            if res.status_code == 200:
                data = res.json()
                content = data.get("message", {}).get("content", "").strip()
                extracted = self._extract_json_from_content(content)
                if extracted and isinstance(extracted, dict) and "speech" in extracted:
                    extracted["offlineActive"] = True
                    return extracted

            # 2. Fallback to generate endpoint
            gen_data = {
                "model": model,
                "prompt": f"{system_prompt}\nUser request: {user_content}\nRespond strictly in valid JSON conforming to schema: speech, state, action, sysCommand.",
                "stream": False,
                "format": "json"
            }
            res = await self.client.post(f"{base_url.rstrip('/')}/api/generate", json=gen_data, timeout=12.0)
            if res.status_code == 200:
                data = res.json()
                content = data.get("response", "").strip()
                extracted = self._extract_json_from_content(content)
                if extracted and isinstance(extracted, dict) and "speech" in extracted:
                    extracted["offlineActive"] = True
                    return extracted
        except Exception as e:
            print(f"[Ollama] Offline query failed: {e}")
        return {}

    async def get_json(self, messages: List[Dict], req) -> Dict:
        """Fetch JSON from primary selected provider with auto-fallback to providers with valid keys and offline Ollama."""
        primary = getattr(req, "activeProvider", "gemini")
        if getattr(req, "isLocalLlm", False):
            primary = "local"

        provider_funcs = {
            "gemini": self._try_gemini,
            "groq": self._try_groq,
            "openrouter": self._try_openrouter,
            "github": self._try_github,
            "nvidia": self._try_nvidia,
            "cerebras": self._try_cerebras,
            "openai": self._try_openai,
            "local": self._try_ollama,
            "ollama": self._try_ollama
        }

        # Check which providers have API keys available
        def has_key(p: str) -> bool:
            if p in ["local", "ollama"]:
                return True
            elif p == "gemini":
                return bool(getattr(req, "geminiKey", None) or os.getenv("GEMINI_API_KEY"))
            elif p == "groq":
                return bool(getattr(req, "groqKey", None) or os.getenv("GROQ_API_KEY"))
            elif p == "openai":
                return bool(getattr(req, "openaiKey", None) or os.getenv("OPENAI_API_KEY"))
            elif p == "openrouter":
                return bool(getattr(req, "openRouterKey", None) or os.getenv("OPENROUTER_API_KEY"))
            elif p == "github":
                return bool(getattr(req, "githubToken", None) or os.getenv("GITHUB_TOKEN"))
            elif p == "nvidia":
                return bool(getattr(req, "nvidiaKey", None) or os.getenv("NVIDIA_NIM_API_KEY"))
            elif p == "cerebras":
                return bool(getattr(req, "cerebrasKey", None) or os.getenv("CEREBRAS_API_KEY"))
            return False

        keyed_providers = [p for p in provider_funcs if has_key(p)]

        if primary in keyed_providers:
            order = [primary] + [p for p in keyed_providers if p != primary]
        elif keyed_providers:
            order = keyed_providers
        else:
            order = [primary] + [p for p in provider_funcs if p != primary]

        for p in order:
            func = provider_funcs.get(p)
            if func:
                try:
                    res = await func(messages, req)
                    if res and isinstance(res, dict) and "speech" in res and res["speech"].strip():
                        return res
                except Exception as e:
                    print(f"[{p}] Provider execution exception: {e}")

        # AUTO-SWITCH TO LOCAL OLLAMA IF ALL CLOUD PROVIDERS FAILED (Offline resilience)
        try:
            print("[AUTO-SWITCH] Cloud providers unavailable. Engaging local Ollama...")
            ollama_res = await self._try_ollama(messages, req)
            if ollama_res and isinstance(ollama_res, dict) and "speech" in ollama_res and ollama_res["speech"].strip():
                logs = ollama_res.get("logs", [])
                logs.append("[AUTO-SWITCH] Offline Local LLM Active (Ollama luna-2.5b)")
                ollama_res["logs"] = logs
                return ollama_res
        except Exception as o_err:
            print(f"[AUTO-SWITCH] Local Ollama fallback error: {o_err}")

        # Conversational fallback if all API calls fail or keys missing
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        msg_strip = last_user_msg.strip().lower()
        greeting_words = {
            "hi", "hello", "hey", "hi luna", "hello luna", "hey luna",
            "greetings", "good morning", "good afternoon", "good evening",
            "who are you", "who are you?", "who are you luna", "who are you luna?",
            "introduce yourself", "introduce yourself luna", "what can you do", "what can you do?"
        }
        if msg_strip in greeting_words or (any(msg_strip.startswith(g + " ") for g in ["hi", "hello", "hey"]) and len(msg_strip.split()) <= 3):
            return {
                "state": "Speaking",
                "speech": "Hello! I am Luna — an advanced autonomous AI operating system and intelligent workstation companion. I'm engineered for deep Linux system control, cybersecurity workflows, full-stack software architecture, and high-performance automation. All neural subsystems are online and operating at peak efficiency. What are we conquering today?",
                "action": "NONE",
                "sysCommand": "",
                "logs": ["[GREETING] Luna self-introduction protocol online"]
            }

        return {
            "state": "Speaking",
            "speech": f"I received your query: '{last_user_msg}'. My AI model could not be contacted directly. Please verify that your GEMINI_API_KEY or provider key is configured properly in .env or the Settings panel.",
            "action": "NONE",
            "sysCommand": "",
            "logs": ["[FALLBACK] All AI model providers unavailable"]
        }

    async def stream_chat(self, prompt: str, context: dict, req) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": "You are LUNA."}, {"role": "user", "content": prompt}]
        res = await self.get_json(messages, req)
        content = res.get("speech", "No response generated.")

        for word in content.split():
            yield word + " "
            await asyncio.sleep(0.02)
