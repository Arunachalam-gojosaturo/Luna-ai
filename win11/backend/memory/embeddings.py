import os
import httpx
from sqlalchemy.future import select
from pgvector.sqlalchemy import Vector
from backend.memory.db import AsyncSessionLocal, Conversation, Memory

# Fallback basic embedding generator using local models or Gemini API
async def generate_embedding(text: str) -> list[float]:
    # Placeholder: Ideally uses HuggingFace local models (sentence-transformers)
    # or Gemini embedding API
    # Since we are trying to optimize and run in Python, we'll hit an API if available.
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        async with httpx.AsyncClient() as client:
            try:
                # Approximate dimensions matching Vector(768)
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={gemini_key}",
                    json={"model": "models/embedding-001", "content": {"parts": [{"text": text}]}}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data['embedding']['values']
            except Exception as e:
                print(f"Embedding generation error: {e}")
                
    # Fallback mock embedding for environments without API key or local model
    return [0.0] * 768

async def save_conversation(session_id: str, role: str, content: str):
    async with AsyncSessionLocal() as session:
        embedding = await generate_embedding(content)
        msg = Conversation(
            session_id=session_id,
            role=role,
            content=content,
            embedding=embedding,
            token_count=len(content.split()) # Naive token count
        )
        session.add(msg)
        await session.commit()

async def semantic_search_memory(query: str, limit: int = 5):
    async with AsyncSessionLocal() as session:
        query_embedding = await generate_embedding(query)
        # Cosine distance
        stmt = select(Memory).order_by(Memory.embedding.cosine_distance(query_embedding)).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
