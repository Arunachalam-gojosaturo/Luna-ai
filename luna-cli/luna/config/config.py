"""
Configuration management for LUNA CLI.
Handles ~/.config/luna/ configuration files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import platformdirs


@dataclass
class ProviderConfig:
    """Provider configuration."""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    

@dataclass
class LunaConfig:
    """Main LUNA configuration."""
    default_provider: str = "groq"
    default_model: Optional[str] = None
    auto_execute: bool = False
    syntax_highlighting: bool = True
    streaming: bool = True
    markdown: bool = True


class ConfigManager:
    """Manages LUNA configuration."""
    
    CONFIG_DIR = Path(platformdirs.user_config_dir("luna", "luna"))
    CONFIG_FILE = CONFIG_DIR / "config.json"
    PROVIDERS_FILE = CONFIG_DIR / "providers.json"
    TRUSTED_WORKSPACES_FILE = CONFIG_DIR / "trusted_workspaces.json"
    SESSIONS_FILE = CONFIG_DIR / "sessions.json"
    
    def __init__(self):
        """Initialize config manager."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.providers = self._load_providers()
        self.trusted_workspaces = self._load_trusted_workspaces()
        
    def _load_config(self) -> LunaConfig:
        """Load main config."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    data = json.load(f)
                    return LunaConfig(**data)
            except Exception:
                pass
        return LunaConfig()
    
    def _load_providers(self) -> Dict[str, ProviderConfig]:
        """Load provider configs."""
        if self.PROVIDERS_FILE.exists():
            try:
                with open(self.PROVIDERS_FILE) as f:
                    data = json.load(f)
                    return {
                        name: ProviderConfig(**cfg) 
                        for name, cfg in data.items()
                    }
            except Exception:
                pass
        return {}
    
    def _load_trusted_workspaces(self) -> list:
        """Load trusted workspaces."""
        if self.TRUSTED_WORKSPACES_FILE.exists():
            try:
                with open(self.TRUSTED_WORKSPACES_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def save_config(self):
        """Save main config."""
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
    
    def save_providers(self):
        """Save provider configs."""
        with open(self.PROVIDERS_FILE, 'w') as f:
            data = {
                name: asdict(cfg) 
                for name, cfg in self.providers.items()
            }
            json.dump(data, f, indent=2)
    
    def add_provider(self, name: str, api_key: str, **kwargs):
        """Add or update provider."""
        self.providers[name] = ProviderConfig(
            name=name, 
            api_key=api_key,
            **kwargs
        )
        self.save_providers()
    
    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get provider config."""
        return self.providers.get(name)
    
    def set_default_provider(self, name: str):
        """Set default provider."""
        if name in self.providers:
            self.config.default_provider = name
            self.save_config()
    
    def trust_workspace(self, path: str):
        """Trust a workspace."""
        if path not in self.trusted_workspaces:
            self.trusted_workspaces.append(path)
            with open(self.TRUSTED_WORKSPACES_FILE, 'w') as f:
                json.dump(self.trusted_workspaces, f, indent=2)
    
    def is_trusted(self, path: str) -> bool:
        """Check if workspace is trusted."""
        return str(path) in self.trusted_workspaces


# Global config instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
