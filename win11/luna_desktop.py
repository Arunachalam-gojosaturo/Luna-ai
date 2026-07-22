#!/usr/bin/env python3
"""
Luna AI - Native Windows 11 Desktop Application Launcher (PyQt6 GUI Window)
Renders a 100% native Windows 11 desktop application window with zero browser chrome, address bar, or tabs.
"""

import os
import sys
import time
import socket
import subprocess
import platform
from pathlib import Path

os.environ["QT_WEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --autoplay-policy=no-user-gesture-required --enable-features=NetworkService,NetworkServiceInProcess"

BASE_DIR = Path(__file__).parent.resolve()

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    VENV_PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"
    VENV_UVICORN = BASE_DIR / "venv" / "Scripts" / "uvicorn.exe"
    NPX_CMD = "npx.cmd"
else:
    VENV_PYTHON = BASE_DIR / "venv" / "bin" / "python"
    VENV_UVICORN = BASE_DIR / "venv" / "bin" / "uvicorn"
    NPX_CMD = "npx"

if not VENV_PYTHON.exists():
    VENV_PYTHON = sys.executable

def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False

def ensure_services():
    processes = []
    
    # 1. Start FastAPI Backend on port 3000 if not running
    if not is_port_open("127.0.0.1", 3000):
        print("[Desktop Application] Starting FastAPI backend on http://127.0.0.1:3000 ...")
        cmd_backend = [str(VENV_UVICORN) if VENV_UVICORN.exists() else sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "3000"] if not VENV_UVICORN.exists() else [str(VENV_UVICORN), "backend.main:app", "--host", "0.0.0.0", "--port", "3000"]
        proc_backend = subprocess.Popen(
            cmd_backend,
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=IS_WINDOWS
        )
        processes.append(proc_backend)

    # 2. Start Vite Dev Server on port 5173 if not running
    if not is_port_open("127.0.0.1", 5173):
        print("[Desktop Application] Starting Vite frontend on http://127.0.0.1:5173 ...")
        proc_vite = subprocess.Popen(
            [NPX_CMD, "vite"],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=IS_WINDOWS
        )
        processes.append(proc_vite)

    # Wait for both FastAPI backend & Vite frontend to become responsive
    print("[Desktop Application] Initializing Luna OS Core Services...")
    for _ in range(40):
        if is_port_open("127.0.0.1", 3000) and is_port_open("127.0.0.1", 5173):
            print("[Desktop Application] Core Services Online!")
            break
        time.sleep(0.5)

    return processes

def launch_native_qt_app():
    procs = ensure_services()
    url = "http://127.0.0.1:5173"

    print("[Desktop Application] Opening Luna AI Native Application Window...")
    
    try:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtWidgets import QApplication, QMainWindow
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebEngineCore import QWebEngineSettings
        from PyQt6.QtGui import QIcon

        app = QApplication(sys.argv)
        app.setApplicationName("Luna AI")
        app.setDesktopFileName("Luna-AI")

        window = QMainWindow()
        window.setWindowTitle("Luna AI | Autonomous Personal AI Operating System (Windows 11)")
        window.resize(1340, 850)

        icon_path = str(BASE_DIR / "public" / "deskopticon.png")
        if not os.path.exists(icon_path):
            icon_path = str(BASE_DIR / "assets" / "deskopticon.png")
        if os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))

        web_view = QWebEngineView()
        
        # Configure WebEngine Settings for full media, video playback, and local file permissions
        settings = web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)

        web_view.setUrl(QUrl(url))
        window.setCentralWidget(web_view)

        window.show()
        exit_code = app.exec()
    except Exception as e:
        print(f"[Desktop Application] Native Qt Window fallback error: {e}")
        exit_code = 1
        try:
            if IS_WINDOWS:
                os.startfile(url)
            else:
                subprocess.run(["xdg-open", url])
        except Exception as e2:
            print(f"[Desktop Application] Failed to launch window: {e2}")

    # Terminate child processes when application window is closed
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass

    sys.exit(exit_code)

if __name__ == "__main__":
    launch_native_qt_app()
