"""
Chat system with streaming and history management.
"""

import asyncio
from datetime import datetime
from typing import Optional, AsyncIterator
from pathlib import Path
import json
import platformdirs
from dataclasses import dataclass, asdict

from luna.providers import BaseProvider, ProviderRegistry, Message, ChatResponse


@dataclass
class ChatMessage:
    """Chat message with metadata."""
    role: str
    content: str
    timestamp: str
    tokens: int = 0


@dataclass
class ChatSession:
    """Chat session metadata."""
    id: str
    created_at: str
    updated_at: str
    provider: str
    model: str
    messages: list[ChatMessage]


class ChatHistory:
    """Manage chat history and sessions."""
    
    HISTORY_DIR = Path(platformdirs.user_data_dir("luna", "luna")) / "history"
    
    def __init__(self):
        """Initialize chat history."""
        self.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session: ChatSession):
        """Save chat session."""
        session_file = self.HISTORY_DIR / f"{session.id}.json"
        session.updated_at = datetime.now().isoformat()
        with open(session_file, 'w') as f:
            json.dump(asdict(session), f, indent=2)
    
    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load chat session."""
        session_file = self.HISTORY_DIR / f"{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    data["messages"] = [ChatMessage(**m) for m in data["messages"]]
                    return ChatSession(**data)
            except Exception:
                pass
        return None
    
    def list_sessions(self, limit: int = 50) -> list[str]:
        """List recent sessions."""
        sessions = sorted(
            self.HISTORY_DIR.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        return [s.stem for s in sessions[:limit]]


class ChatSystem:
    """Main chat system with streaming support."""
    
    def __init__(self, provider: BaseProvider):
        """Initialize chat system."""
        self.provider = provider
        self.history = ChatHistory()
        self.current_session: Optional[ChatSession] = None
        self.messages: list[Message] = []
    
    def new_session(self, session_id: str, provider_name: str, model: str):
        """Start new chat session."""
        self.current_session = ChatSession(
            id=session_id,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            provider=provider_name,
            model=model,
            messages=[]
        )
        self.messages = []
    
    def load_session(self, session_id: str):
        """Load existing session."""
        session = self.history.load_session(session_id)
        if session:
            self.current_session = session
            self.messages = [
                Message(role=m.role, content=m.content)
                for m in session.messages
            ]
            return True
        return False
    
    def add_message(self, role: str, content: str) -> Message:
        """Add message to session."""
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        
        if self.current_session:
            self.current_session.messages.append(
                ChatMessage(
                    role=role,
                    content=content,
                    timestamp=datetime.now().isoformat()
                )
            )
        
        return msg
    
    async def chat(self, user_message: str, **kwargs) -> ChatResponse:
        """Send message and get response."""
        self.add_message("user", user_message)
        response = await self.provider.chat(self.messages, **kwargs)
        self.add_message("assistant", response.content)
        
        if self.current_session:
            self.history.save_session(self.current_session)
        
        return response
    
    async def stream_chat(
        self, 
        user_message: str, 
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response."""
        self.add_message("user", user_message)
        
        full_response = ""
        async for chunk in self.provider.stream_chat(self.messages, **kwargs):
            full_response += chunk
            yield chunk
        
        self.add_message("assistant", full_response)
        
        if self.current_session:
            self.history.save_session(self.current_session)
    
    def get_messages(self) -> list[Message]:
        """Get current messages."""
        return self.messages
    
    def clear_session(self):
        """Clear current session."""
        self.messages = []
        self.current_session = None
    
    def export_session(self) -> Optional[str]:
        """Export current session as markdown."""
        if not self.current_session:
            return None
        
        lines = [
            f"# Chat Session: {self.current_session.id}",
            f"Provider: {self.current_session.provider}",
            f"Model: {self.current_session.model}",
            f"Created: {self.current_session.created_at}",
            "",
        ]
        
        for msg in self.current_session.messages:
            role = "🤖 Assistant" if msg.role == "assistant" else "👤 You"
            lines.append(f"## {role}")
            lines.append(msg.content)
            lines.append("")
        
        return "\n".join(lines)
