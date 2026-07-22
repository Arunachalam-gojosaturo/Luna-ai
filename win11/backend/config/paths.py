"""
XDG-compliant path resolution for Luna OS.
Handles database, cache, and config locations properly on Arch Linux.
"""

import os
from pathlib import Path


def get_data_dir() -> Path:
    """
    Get Windows %LOCALAPPDATA%\LunaAI or XDG_DATA_HOME path
    Used for databases, cache, runtime data
    """
    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        data_dir = Path(local_app_data) / 'LunaAI'
    else:
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
            data_dir = Path(xdg_data) / 'luna-os'
        else:
            data_dir = Path.home() / 'AppData' / 'Local' / 'LunaAI'
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    """
    Get Windows %APPDATA%\LunaAI or XDG_CONFIG_HOME path
    Used for configuration files
    """
    app_data = os.environ.get('APPDATA')
    if app_data:
        config_dir = Path(app_data) / 'LunaAI'
    else:
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            config_dir = Path(xdg_config) / 'luna-os'
        else:
            config_dir = Path.home() / 'AppData' / 'Roaming' / 'LunaAI'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cache_dir() -> Path:
    """
    Get Windows %TEMP%\LunaAI or XDG_CACHE_HOME path
    Used for temporary files and cache
    """
    temp_dir = os.environ.get('TEMP') or os.environ.get('TMP')
    if temp_dir:
        cache_dir = Path(temp_dir) / 'LunaAI'
    else:
        xdg_cache = os.environ.get('XDG_CACHE_HOME')
        if xdg_cache:
            cache_dir = Path(xdg_cache) / 'luna-os'
        else:
            cache_dir = Path.home() / 'AppData' / 'Local' / 'Temp' / 'LunaAI'
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_database_path() -> Path:
    """Get path to SQLite chat history database"""
    db_path = get_data_dir() / 'luna_chat.db'
    return db_path


def get_chroma_db_path() -> Path:
    """Get path to ChromaDB vector database"""
    chroma_path = get_data_dir() / 'luna_chroma_db'
    chroma_path.mkdir(parents=True, exist_ok=True)
    return chroma_path


def get_log_dir() -> Path:
    """Get path to log files"""
    log_dir = get_cache_dir() / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_project_root() -> Path:
    """
    Get the project root directory.
    Works in development and installed contexts.
    """
    # Try to find backend module
    try:
        import backend
        return Path(backend.__file__).parent.parent
    except ImportError:
        pass
    
    # Fallback: assume script is in backend/
    return Path(__file__).parent.parent.parent
