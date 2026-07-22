import chromadb
from typing import List, Dict, Any
from backend.config.paths import get_chroma_db_path

class LongTermMemory:
    """
    Semantic Memory using ChromaDB for persistent storage.
    """
    def __init__(self):
        # Local persistent ChromaDB instance
        self.db_path = str(get_chroma_db_path())
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(name="conversations")
        except Exception as e:
            print(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None

    async def save_interaction(self, session_id: str, role: str, content: str):
        if not self.collection: return
        
        # In a real app, generate proper IDs
        import os
        doc_id = f"{session_id}_{os.urandom(4).hex()}"
        
        try:
            self.collection.add(
                documents=[content],
                metadatas=[{"role": role, "session_id": session_id}],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"Memory save error: {e}")

    async def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.collection: return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            memories = []
            if results and results['documents'] and results['documents'][0]:
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    memories.append({"content": doc, "role": meta.get("role", "unknown")})
            return memories
        except Exception as e:
            print(f"Memory search error: {e}")
            return []

long_term_memory = LongTermMemory()
