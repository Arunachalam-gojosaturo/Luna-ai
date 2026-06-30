import os
import json
import httpx
import asyncio
from typing import Dict, Any, List

class ProviderManager:
    def __init__(self):
        self.default_openai_model = "gpt-4o-mini"
        self.default_groq_model = "llama3-70b-8192"
        self.default_gemini_model = "gemini-2.5-flash"
        
        # Async HTTP client pool for low latency
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
    async def close(self):
        await self.client.aclose()

    async def _post_json(self, url: str, headers: dict, data: dict) -> dict:
        try:
            resp = await self.client.post(url, headers=headers, json=data)
            if resp.status_code == 429:
                print("Rate limit hit, backing off...")
                await asyncio.sleep(2)
                resp = await self.client.post(url, headers=headers, json=data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Provider request error: {e}")
            return {}

    async def _try_openai(self, messages: List[Dict], req) -> Dict:
        if not req.openaiKey: return {}
        headers = {"Authorization": f"Bearer {req.openaiKey}", "Content-Type": "application/json"}
        data = {
            "model": req.modelSelection or self.default_openai_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        res = await self._post_json("https://api.openai.com/v1/chat/completions", headers, data)
        if res and "choices" in res:
            return json.loads(res["choices"][0]["message"]["content"].strip())
        return {}

    async def _try_groq(self, messages: List[Dict], req) -> Dict:
        if not req.groqKey: return {}
        headers = {"Authorization": f"Bearer {req.groqKey}", "Content-Type": "application/json"}
        data = {
            "model": req.modelSelection or self.default_groq_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        res = await self._post_json("https://api.groq.com/openai/v1/chat/completions", headers, data)
        if res and "choices" in res:
            return json.loads(res["choices"][0]["message"]["content"].strip())
        return {}

    async def _try_gemini(self, messages: List[Dict], req) -> Dict:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key: return {}
        
        gemini_msgs = []
        for msg in messages:
            gemini_msgs.append({
                "role": "user" if msg["role"] in ["system", "user"] else "model",
                "parts": [{"text": msg["content"]}]
            })
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.default_gemini_model}:generateContent?key={gemini_key}"
        data = {
            "contents": gemini_msgs,
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        res = await self._post_json(url, {}, data)
        if res and "candidates" in res:
            return json.loads(res["candidates"][0]["content"]["parts"][0]["text"].strip())
        return {}

    async def generate_response(self, messages: List[Dict], req) -> Dict:
        # Fallback cascade logic
        result = await self._try_groq(messages, req)
        if result: return result
        
        result = await self._try_gemini(messages, req)
        if result: return result
        
        result = await self._try_openai(messages, req)
        if result: return result

        # Fallback local dummy response
        return {
            "state": "Speaking",
            "speech": "All providers failed. I processed this locally via Python fallback.",
            "action": "NONE",
            "targetDevice": "NONE",
            "logs": ["Local python backend processing fallback."],
            "notifications": ["API Providers unavailable."]
        }
