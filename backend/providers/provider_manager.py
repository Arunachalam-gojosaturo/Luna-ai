import os
import json
import httpx
import asyncio
import time
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
        start_time = time.time()
        try:
            resp = await self.client.post(url, headers=headers, json=data)
            if resp.status_code == 429:
                await asyncio.sleep(2)
                resp = await self.client.post(url, headers=headers, json=data)
            resp.raise_for_status()
            
            latency = time.time() - start_time
            self.stats[provider]["latency"].append(latency)
            return resp.json()
        except Exception as e:
            self.stats[provider]["failures"] += 1
            if hasattr(e, 'response'):
                print(f"[{provider}] Provider error: {e}. Body: {e.response.text}")
            else:
                print(f"[{provider}] Provider error: {e}")
            return {}

    async def get_json(self, messages: List[Dict], req) -> Dict:
        """Fetch JSON from the selected provider, fallback if failed"""
        
        provider = getattr(req, "activeProvider", "groq")
        
        # 1. Groq
        if provider == "groq" and req.groqKey:
            headers = {"Authorization": f"Bearer {req.groqKey}", "Content-Type": "application/json"}
            data = {
                "model": req.modelSelection or self.default_groq_model,
                "messages": messages,
                "temperature": 0.2
            }
            res = await self._post_json("https://api.groq.com/openai/v1/chat/completions", headers, data, "groq")
            if res and "choices" in res:
                content = res["choices"][0]["message"]["content"].strip()
                if content.startswith("```json"):
                    content = content[7:].strip()
                if content.endswith("```"):
                    content = content[:-3].strip()
                return json.loads(content)
                
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
                    return json.loads(res["candidates"][0]["content"]["parts"][0]["text"].strip())

        # 3. OpenAI
        if provider == "openai" and req.openaiKey:
            headers = {"Authorization": f"Bearer {req.openaiKey}", "Content-Type": "application/json"}
            data = {
                "model": req.modelSelection or self.default_openai_model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }
            res = await self._post_json("https://api.openai.com/v1/chat/completions", headers, data, "openai")
            if res and "choices" in res:
                return json.loads(res["choices"][0]["message"]["content"].strip())

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
