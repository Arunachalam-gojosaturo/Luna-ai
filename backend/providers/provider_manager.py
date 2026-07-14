import os
import json
import httpx
import asyncio
import time
import re
from typing import Dict, Any, List, AsyncGenerator

class ProviderManager:
    def __init__(self):
        self.default_openai_model = "gpt-4o-mini"
        self.default_groq_model = "llama-3.3-70b-versatile"
        self.default_gemini_model = "gemini-2.5-flash"
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        # Latency tracking
        self.stats = {
            "groq": {"latency": [], "tokens": 0, "failures": 0},
            "gemini": {"latency": [], "tokens": 0, "failures": 0},
            "openai": {"latency": [], "tokens": 0, "failures": 0}
        }
        
    async def close(self):
        await self.client.aclose()

    async def _post_json(self, url: str, headers: dict, data: dict, provider: str) -> dict:
        """Post request with exponential backoff retry for rate limits."""
        start_time = time.time()
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                resp = await self.client.post(url, headers=headers, json=data)
                
                if resp.status_code == 429:
                    # Rate limited - use exponential backoff
                    wait_time = min(2 ** attempt, 30)  # Cap at 30 seconds
                    print(f"[{provider}] Rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                    
                resp.raise_for_status()
                
                latency = time.time() - start_time
                self.stats[provider]["latency"].append(latency)
                return resp.json()
            except Exception as e:
                if attempt == max_retries - 1:
                    self.stats[provider]["failures"] += 1
                    print(f"[{provider}] Provider error (final attempt): {e}")
                    return {}
                # Retry on other errors
                await asyncio.sleep(2 ** attempt)
        
        return {}

    def _extract_json_from_content(self, content: str) -> Dict[str, Any] | None:
        """Safely extract JSON from potentially wrapped content."""
        try:
            # Try direct JSON parsing first
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try markdown code block extraction
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None

    async def get_json(self, messages: List[Dict], req) -> Dict:
        """Fetch JSON from the selected provider, fallback if failed"""
        
        provider = getattr(req, "activeProvider", "groq")

        # 0. Local LLM (Ollama) via LiteLLM
        if provider == "local":
            try:
                import litellm
                local_url = getattr(req, "localLlmUrl", "http://localhost:11434")
                local_model = getattr(req, "localLlmModel", "llama3")
                
                loop = asyncio.get_event_loop()
                # Run completion in executor to keep it async friendly
                response = await loop.run_in_executor(
                    None,
                    lambda: litellm.completion(
                        model=f"ollama/{local_model}",
                        messages=messages,
                        api_base=local_url,
                        temperature=0.2
                    )
                )
                content = response.choices[0].message.content.strip()
                parsed = self._extract_json_from_content(content)
                if parsed:
                    return parsed
            except Exception as e:
                print(f"[litellm-local] Error: {e}")

        # 0.5. Open Claw Connector via LiteLLM
        if provider == "openclaw":
            try:
                import litellm
                claw_url = getattr(req, "openClawUrl", "http://localhost:8000/v1")
                claw_key = getattr(req, "openClawApiKey", "default-key")
                claw_model = getattr(req, "modelSelection", "gpt-3.5-turbo") or "gpt-3.5-turbo"
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: litellm.completion(
                        model=f"openai/{claw_model}",
                        messages=messages,
                        api_base=claw_url,
                        api_key=claw_key,
                        temperature=0.3
                    )
                )
                content = response.choices[0].message.content.strip()
                parsed = self._extract_json_from_content(content)
                if parsed:
                    return parsed
            except Exception as e:
                print(f"[litellm-openclaw] Error: {e}")
        
        # 1. Groq
        if provider == "groq" and getattr(req, "groqKey", None):
            headers = {"Authorization": f"Bearer {req.groqKey}", "Content-Type": "application/json"}
            data = {
                "model": req.modelSelection or self.default_groq_model,
                "messages": messages,
                "temperature": 0.2
            }
            res = await self._post_json("https://api.groq.com/openai/v1/chat/completions", headers, data, "groq")
            if res and "choices" in res:
                try:
                    content = res["choices"][0]["message"]["content"].strip()
                    parsed = self._extract_json_from_content(content)
                    if parsed:
                        return parsed
                except (KeyError, IndexError, ValueError) as e:
                    print(f"[groq] Failed to parse response: {e}")
                
        # 2. Gemini
        if provider == "gemini":
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                gemini_msgs = []
                for msg in messages:
                    gemini_msgs.append({
                        "role": "user" if msg["role"] in ["system", "user"] else "model",
                        "parts": [{"text": msg["content"]}]
                    })
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.default_gemini_model}:generateContent?key={gemini_key}"
                data = {
                    "contents": gemini_msgs,
                    "generationConfig": {"responseMimeType": "application/json"}
                }
                res = await self._post_json(url, {}, data, "gemini")
                if res and "candidates" in res:
                    try:
                        content = res["candidates"][0]["content"]["parts"][0]["text"].strip()
                        parsed = self._extract_json_from_content(content)
                        if parsed:
                            return parsed
                    except (KeyError, IndexError, ValueError) as e:
                        print(f"[gemini] Failed to parse response: {e}")

        # 3. OpenAI
        if provider == "openai" and getattr(req, "openaiKey", None):
            headers = {"Authorization": f"Bearer {req.openaiKey}", "Content-Type": "application/json"}
            data = {
                "model": req.modelSelection or self.default_openai_model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }
            res = await self._post_json("https://api.openai.com/v1/chat/completions", headers, data, "openai")
            if res and "choices" in res:
                try:
                    content = res["choices"][0]["message"]["content"].strip()
                    parsed = self._extract_json_from_content(content)
                    if parsed:
                        return parsed
                except (KeyError, IndexError, ValueError) as e:
                    print(f"[openai] Failed to parse response: {e}")

        return {}

    async def stream_chat(self, prompt: str, context: dict, req) -> AsyncGenerator[str, None]:
        """Streaming response using Unified Async Generator"""
        # For Phase 1, we just simulate streaming with the fastest provider or fallback
        # In actual implementation, you'd use httpx async streaming
        messages = [{"role": "system", "content": "You are LUNA."}, {"role": "user", "content": prompt}]
        # For simplicity, returning a chunked string of the result.
        res = await self.get_json(messages, req)
        content = res.get("speech", "No response generated.")
        
        # Simulate streaming chunk by chunk
        for word in content.split():
            yield word + " "
            await asyncio.sleep(0.02)
