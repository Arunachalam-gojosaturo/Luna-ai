"""
Luna CLI Configuration and Advanced Features
Handles CLI settings, profiles, and advanced command modes
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
import hashlib


@dataclass
class CLIProfile:
    """User CLI profile configuration"""
    name: str
    model: str = "groq"
    provider: str = "groq"
    voice_enabled: bool = True
    auto_confirm: bool = False
    theme: str = "dark"
    history_size: int = 1000
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class CLISettings:
    """Global CLI settings"""
    debug_mode: bool = False
    auto_save_history: bool = True
    history_persistence: bool = True
    default_timeout: int = 60
    max_retries: int = 3
    verbose_output: bool = False
    animations_enabled: bool = True
    colorize_output: bool = True
    prompt_confirmations: bool = True
    web_search_enabled: bool = False
    plugin_directory: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class ConfigManager:
    """Manages CLI configuration"""
    
    CONFIG_DIR = Path.home() / ".luna" / "cli"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    PROFILES_FILE = CONFIG_DIR / "profiles.json"
    HISTORY_FILE = CONFIG_DIR / "history.json"
    CACHE_DIR = CONFIG_DIR / "cache"
    
    def __init__(self):
        """Initialize config manager"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        self.settings = self._load_settings()
        self.profiles = self._load_profiles()
        self.current_profile = self._get_default_profile()
    
    def _load_settings(self) -> CLISettings:
        """Load settings from file"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    data = json.load(f)
                    return CLISettings(**data)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        return CLISettings()
    
    def _load_profiles(self) -> Dict[str, CLIProfile]:
        """Load profiles from file"""
        if self.PROFILES_FILE.exists():
            try:
                with open(self.PROFILES_FILE) as f:
                    data = json.load(f)
                    return {name: CLIProfile(**profile) for name, profile in data.items()}
            except Exception as e:
                print(f"Error loading profiles: {e}")
        
        # Create default profile
        default = CLIProfile(name="default")
        self.save_profile(default)
        return {"default": default}
    
    def _get_default_profile(self) -> CLIProfile:
        """Get default profile"""
        return self.profiles.get("default", CLIProfile(name="default"))
    
    def save_settings(self) -> bool:
        """Save settings to file"""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def save_profile(self, profile: CLIProfile) -> bool:
        """Save a profile"""
        try:
            self.profiles[profile.name] = profile
            with open(self.PROFILES_FILE, 'w') as f:
                data = {name: profile.to_dict() for name, profile in self.profiles.items()}
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
    
    def create_profile(self, name: str, **kwargs) -> CLIProfile:
        """Create a new profile"""
        profile = CLIProfile(name=name, **kwargs)
        self.save_profile(profile)
        return profile
    
    def get_profile(self, name: str) -> Optional[CLIProfile]:
        """Get a profile by name"""
        return self.profiles.get(name)
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile"""
        if name == "default":
            return False  # Cannot delete default profile
        
        if name in self.profiles:
            del self.profiles[name]
            self._save_profiles()
            return True
        return False
    
    def switch_profile(self, name: str) -> bool:
        """Switch to a different profile"""
        profile = self.get_profile(name)
        if profile:
            self.current_profile = profile
            return True
        return False
    
    def _save_profiles(self) -> None:
        """Save all profiles"""
        try:
            with open(self.PROFILES_FILE, 'w') as f:
                data = {name: profile.to_dict() for name, profile in self.profiles.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")
    
    def list_profiles(self) -> List[str]:
        """List all profile names"""
        return list(self.profiles.keys())
    
    def get_cache_dir(self) -> Path:
        """Get cache directory"""
        return self.CACHE_DIR
    
    def clear_cache(self) -> bool:
        """Clear cache directory"""
        try:
            import shutil
            shutil.rmtree(self.CACHE_DIR)
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False


class CommandAliasManager:
    """Manages custom command aliases"""
    
    ALIAS_FILE = ConfigManager.CONFIG_DIR / "aliases.json"
    
    def __init__(self):
        """Initialize alias manager"""
        self.aliases = self._load_aliases()
    
    def _load_aliases(self) -> Dict[str, str]:
        """Load aliases from file"""
        if self.ALIAS_FILE.exists():
            try:
                with open(self.ALIAS_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        
        return self._get_default_aliases()
    
    def _get_default_aliases(self) -> Dict[str, str]:
        """Get default aliases"""
        return {
            "h": "help",
            "?": "help",
            "q": "exit",
            "quit": "exit",
            "cls": "clear",
            "s": "status",
            "hist": "history",
            "mem": "memory",
            "v": "voice",
            "m": "model",
        }
    
    def _save_aliases(self) -> None:
        """Save aliases to file"""
        try:
            ConfigManager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.ALIAS_FILE, 'w') as f:
                json.dump(self.aliases, f, indent=2)
        except Exception as e:
            print(f"Error saving aliases: {e}")
    
    def add_alias(self, alias: str, command: str) -> bool:
        """Add a custom alias"""
        if alias and command:
            self.aliases[alias] = command
            self._save_aliases()
            return True
        return False
    
    def remove_alias(self, alias: str) -> bool:
        """Remove an alias"""
        if alias in self.aliases and alias not in self._get_default_aliases():
            del self.aliases[alias]
            self._save_aliases()
            return True
        return False
    
    def get_command(self, alias: str) -> Optional[str]:
        """Get command for alias"""
        return self.aliases.get(alias)
    
    def list_aliases(self) -> Dict[str, str]:
        """List all aliases"""
        return self.aliases.copy()


class HistoryManager:
    """Manages command history"""
    
    HISTORY_FILE = ConfigManager.CONFIG_DIR / "history.json"
    MAX_HISTORY = 10000
    
    def __init__(self):
        """Initialize history manager"""
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file"""
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        
        return []
    
    def _save_history(self) -> None:
        """Save history to file"""
        try:
            ConfigManager.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            # Keep only recent history
            history_to_save = self.history[-self.MAX_HISTORY:]
            with open(self.HISTORY_FILE, 'w') as f:
                json.dump(history_to_save, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_entry(self, command: str, response: str, timestamp: Optional[str] = None) -> None:
        """Add a history entry"""
        entry = {
            "timestamp": timestamp or datetime.now().isoformat(),
            "command": command,
            "response": response,
        }
        self.history.append(entry)
        self._save_history()
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search history"""
        query_lower = query.lower()
        return [h for h in self.history if query_lower in h.get("command", "").lower()]
    
    def get_recent(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent history entries"""
        return self.history[-count:]
    
    def clear(self) -> None:
        """Clear all history"""
        self.history = []
        self._save_history()
    
    def export(self, filepath: str) -> bool:
        """Export history to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.history, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting history: {e}")
            return False


class PluginManager:
    """Manages CLI plugins"""
    
    PLUGINS_DIR = ConfigManager.CONFIG_DIR / "plugins"
    
    def __init__(self):
        """Initialize plugin manager"""
        self.PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        self.plugins: Dict[str, Any] = {}
    
    def load_plugins(self) -> None:
        """Load all plugins from plugins directory"""
        if not self.PLUGINS_DIR.exists():
            return
        
        for plugin_file in self.PLUGINS_DIR.glob("*.py"):
            self._load_plugin(plugin_file)
    
    def _load_plugin(self, filepath: Path) -> None:
        """Load a single plugin"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "initialize"):
                module.initialize()
            
            self.plugins[filepath.stem] = module
        except Exception as e:
            print(f"Error loading plugin {filepath.name}: {e}")
    
    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a plugin"""
        return self.plugins.get(name)
    
    def execute_plugin_command(self, plugin_name: str, command: str) -> Optional[Any]:
        """Execute a command from a plugin"""
        plugin = self.get_plugin(plugin_name)
        if plugin and hasattr(plugin, "execute"):
            return plugin.execute(command)
        return None
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugins"""
        return list(self.plugins.keys())


if __name__ == "__main__":
    # Demo
    print("\n" + "="*60)
    print("CLI Config Manager Demo")
    print("="*60 + "\n")
    
    # Test config manager
    config = ConfigManager()
    print(f"Config Directory: {config.CONFIG_DIR}")
    print(f"Current Profile: {config.current_profile.name}")
    print(f"Model: {config.current_profile.model}")
    print(f"Provider: {config.current_profile.provider}\n")
    
    # Test profiles
    print("Available Profiles:")
    for profile_name in config.list_profiles():
        print(f"  - {profile_name}")
    print()
    
    # Test aliases
    alias_mgr = CommandAliasManager()
    print("Command Aliases:")
    for alias, command in list(alias_mgr.list_aliases().items())[:5]:
        print(f"  {alias:5} -> {command}")
    print()
    
    # Test history
    history_mgr = HistoryManager()
    print(f"History entries: {len(history_mgr.history)}")
    if history_mgr.get_recent(1):
        recent = history_mgr.get_recent(1)[0]
        print(f"Last command: {recent.get('command')}")
