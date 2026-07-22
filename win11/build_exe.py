#!/usr/bin/env python3
"""
Luna AI — Windows 11 PyInstaller Standalone Executable (.exe) Builder
Compiles Luna AI into a standalone executable package for Windows 11.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

def build_windows_exe():
    print("======================================================================")
    print(" 🛠️  Building Standalone Luna AI (.exe) for Windows 11")
    print("======================================================================")

    # 1. Build Vite frontend assets
    print("▸ Step 1/4: Compiling production frontend web assets...")
    subprocess.run(["npm", "run", "build"], cwd=str(BASE_DIR), shell=True, check=True)

    # 2. Ensure PyInstaller is installed
    print("▸ Step 2/4: Verifying PyInstaller availability...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"], check=True)

    # 3. Construct PyInstaller Command
    print("▸ Step 3/4: Packaging Python core and PyQt6 WebEngine into EXE...")
    
    icon_arg = []
    if (BASE_DIR / "public" / "deskopticon.png").exists():
        icon_arg = ["--icon", str(BASE_DIR / "public" / "deskopticon.png")]

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=LunaAI",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--add-data", f"dist;dist",
        "--add-data", f"backend;backend",
        "--add-data", f"public;public",
        "--add-data", f"assets;assets",
    ] + icon_arg + ["luna_desktop.py"]

    subprocess.run(pyinstaller_cmd, cwd=str(BASE_DIR), check=True)

    dist_exe_path = BASE_DIR / "dist" / "LunaAI" / "LunaAI.exe"
    print("======================================================================")
    print(f" ✨ SUCCESS! Windows 11 Executable built successfully!")
    print(f" 📂 Executable Output Path: {dist_exe_path}")
    print("======================================================================")

if __name__ == "__main__":
    build_windows_exe()
