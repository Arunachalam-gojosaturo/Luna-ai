#!/usr/bin/env python3
"""
Luna AI - Arch Linux Desktop Application Runner
Launches Luna AI as a native desktop application on Arch Linux / Hyprland.
"""

import sys
import time
import socket
import subprocess
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = BASE_DIR / "venv" / "bin" / "python"
VENV_UVICORN = BASE_DIR / "venv" / "bin" / "uvicorn"

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
        print("[Desktop Runner] Starting FastAPI backend on http://127.0.0.1:3000 ...")
        proc_backend = subprocess.Popen(
            [str(VENV_UVICORN), "backend.main:app", "--host", "0.0.0.0", "--port", "3000"],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(proc_backend)

    # 2. Start Vite Dev Server on port 5173 if not running
    if not is_port_open("127.0.0.1", 5173):
        print("[Desktop Runner] Starting Vite frontend on http://127.0.0.1:5173 ...")
        proc_vite = subprocess.Popen(
            ["npx", "vite"],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(proc_vite)

    # Wait for both FastAPI backend & Vite frontend to become responsive
    print("[Desktop Runner] Waiting for Luna OS backend & frontend to initialize...")
    for _ in range(40):
        if is_port_open("127.0.0.1", 3000) and is_port_open("127.0.0.1", 5173):
            print("[Desktop Runner] Backend and Frontend are online!")
            break
        time.sleep(0.5)

    return processes

def launch_desktop_app():
    procs = ensure_services()
    url = "http://localhost:5173"

    print("[Desktop Runner] Launching Luna AI Native Arch Linux Application Window...")
    
    # Attempt pywebview native GTK/WebKit GUI window launch
    try:
        import webview
        window = webview.create_window(
            title="Luna AI | Autonomous AI OS",
            url=url,
            width=1280,
            height=820,
            resizable=True,
            text_select=True,
            confirm_close=False
        )
        webview.start(debug=False)
    except Exception as e:
        print(f"[Desktop Runner] pywebview fallback: {e}")
        # Standalone Desktop App Fallback via Firefox on Arch Linux
        try:
            subprocess.run(["firefox", "--new-window", url])
        except Exception as e2:
            print(f"[Desktop Runner] Failed to open desktop window: {e2}")

    # Clean shutdown of spawned child processes on window exit
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    launch_desktop_app()
