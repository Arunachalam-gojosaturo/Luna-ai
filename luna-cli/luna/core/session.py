"""
Session management for LUNA CLI.
Handles workspace, provider, and preferences persistence.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import platformdirs


@dataclass
class SessionState:
    """Session state for LUNA."""
    workspace: str = ""
    provider: str = "groq"
    model: Optional[str] = None
    current_session: Optional[str] = None
    last_used_provider: str = "groq"
    auto_execute: bool = False
    last_command: str = ""
    timestamp: str = ""


class SessionManager:
    """Manage LUNA sessions."""
    
    STATE_DIR = Path(platformdirs.user_state_dir("luna", "luna"))
    STATE_FILE = STATE_DIR / "session.json"
    
    def __init__(self):
        """Initialize session manager."""
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()
    
    def _load_state(self) -> SessionState:
        """Load session state."""
        if self.STATE_FILE.exists():
            try:
                with open(self.STATE_FILE) as f:
                    data = json.load(f)
                    return SessionState(**data)
            except Exception:
                pass
        return SessionState()
    
    def save_state(self):
        """Save session state."""
        self.state.timestamp = datetime.now().isoformat()
        with open(self.STATE_FILE, 'w') as f:
            json.dump(asdict(self.state), f, indent=2)
    
    def set_workspace(self, path: str):
        """Set current workspace."""
        self.state.workspace = path
        self.save_state()
    
    def set_provider(self, provider: str):
        """Set current provider."""
        self.state.provider = provider
        self.state.last_used_provider = provider
        self.save_state()
    
    def set_model(self, model: str):
        """Set model for current provider."""
        self.state.model = model
        self.save_state()
    
    def set_session(self, session_id: str):
        """Set current chat session."""
        self.state.current_session = session_id
        self.save_state()
    
    def get_workspace(self) -> str:
        """Get current workspace."""
        return self.state.workspace or str(Path.cwd())
    
    def get_provider(self) -> str:
        """Get current provider."""
        return self.state.provider
    
    def get_model(self) -> Optional[str]:
        """Get current model."""
        return self.state.model
    
    def get_session(self) -> Optional[str]:
        """Get current session."""
        return self.state.current_session


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
