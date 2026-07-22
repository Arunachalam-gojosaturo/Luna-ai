<div align="center">
  <img src="assets/readme-header.png" alt="Luna AI Windows 11 Header Banner" width="100%" />
  <br/><br/>
  <img src="assets/deskopticon.png" alt="Luna AI Desktop Icon" width="128" />
  <h1>🌙 Luna AI — Windows 11 Edition</h1>
  <p><strong>Next-Generation Autonomous Personal AI Operating System & Voice Companion for Windows 11</strong></p>

  [![Windows 11](https://img.shields.io/badge/Platform-Windows_11-0078D4?logo=windows11)](https://microsoft.com/windows)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
  [![PyQt6](https://img.shields.io/badge/Desktop-PyQt6_QtWebEngine-41CD52?logo=qt)](https://www.qt.io/)
  [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
</div>

---

## 🌌 What is Luna AI (Windows 11 Edition)?

**Luna AI (Windows 11 Edition)** is an autonomous personal AI operating system tailored specifically for **Windows 11**.

It combines continuous voice recognition, real-time audio synthesis, native Windows 11 desktop embedding via PyQt6 QWebEngine, wireless Android (ADB) device management, Windows File Explorer integration, PowerShell system automation, `winget` package management, and multi-provider LLM intelligence routing into one unified desktop application.

---

## ⚡ One-Line PowerShell Installation

Open **PowerShell** as Administrator or standard user and run:

```powershell
iwr -useb https://raw.githubusercontent.com/Arunachalam-gojosaturo/Luna-ai/main/win11/install.ps1 | iex
```

Or double-click `install_win11.bat` inside the `win11` directory!

---

## 🛠️ Building Standalone Executable (.exe) for Windows 11

To compile Luna AI into a standalone executable (`LunaAI.exe`):

```cmd
cd win11
python build_exe.py
```

The output executable will be created at `win11/dist/LunaAI/LunaAI.exe`.

---

## ✨ Features & Windows 11 System Controls

* 🎙️ **Always-On Voice Assistant**: Continuous speech recognition via Groq Whisper (`whisper-large-v3-turbo`) & Google STT.
* 🗣️ **Windows Neural TTS Engine**: Native audio playback via PowerShell `SoundPlayer`, `mpv`, or Microsoft Edge TTS.
* 🪟 **Windows 11 Native Desktop Embedding**:
  * 100% native PyQt6 QWebEngine application window (`LunaAI.exe` / `luna_desktop.py`).
  * Zero browser tabs or address bar.
* 📂 **Windows File Explorer Integration**:
  * Native PowerShell `FolderBrowserDialog` folder picker.
  * Direct launch into `explorer.exe` for viewing files and directories.
* 📦 **winget & Chocolatey Package Management**:
  * Search, install, update, and uninstall Windows software via `winget` and `choco`.
* 📱 **Wireless Android ADB Bridge**:
  * Wireless ADB discovery, remote device unlock, touch input control, and `scrcpy` screen mirroring.
* 💻 **Dual GUI & CLI Interfaces**:
  * **GUI Window**: Launched via `luna-ai.bat` or `luna.bat`.
  * **CLI Mode**: Launched via `luna-cli.bat` with VT100 ANSI color support.

---

## 📂 Windows 11 Folder Structure

```
win11/
├── assets/
│   ├── deskopticon.png             # Official Luna AI Desktop Icon
│   └── readme-header.png           # Header Banner Image
├── backend/                        # Python FastAPI AI Core for Windows 11
│   ├── agents/                     # Windows System & Microservice Agents
│   │   ├── linux_agent.py          # Windows 11 / PowerShell Command Execution Agent
│   │   ├── package_manager.py      # winget & choco Package Manager Agent
│   │   ├── system.py               # Re-exported System Agent Module
│   │   └── whatsapp_agent.py       # WhatsApp Web Automation Agent
│   ├── api/                        # REST & WebSocket API Routers
│   │   ├── agents.py               # Microservice Agent Endpoints
│   │   ├── routes.py               # Core Luna Execution & Windows Folder Picker Routes
│   │   └── ws.py                   # WebSocket Real-Time Event Listener
│   ├── config/                     # %LOCALAPPDATA%\LunaAI Path Resolvers
│   │   └── paths.py                # Windows AppData Directory Paths
│   ├── core/                       # Brain Intelligence & Decision Framework
│   │   ├── brain.py / brain_v2.py  # LunaBrain Intelligence Engine
│   │   ├── planner.py              # Adaptive Planning Engine
│   │   └── voice_agent.py          # Microphone Listener & VAD Pipeline
│   ├── utils/                      # Windows 11 PowerShell Controls
│   │   ├── sys_control.py          # Win32 & PowerShell Volume/Brightness/Power Controls
│   │   └── adb_manager.py          # Wireless Android ADB Controller
│   └── main.py                     # FastAPI Server Entry Point (Port 3000)
├── public/                         # Static Assets
│   ├── background.png              # UI Background Image
│   └── deskopticon.png             # Application Icon
├── src/                            # React 19 Frontend UI
├── build_exe.py                    # PyInstaller Standalone .exe Builder
├── install.ps1                     # PowerShell Automated Installer
├── install_win11.bat               # Double-Click Batch Installer
├── luna_cli_enhanced.py            # Terminal CLI Interface for Windows
├── luna_desktop.py                 # PyQt6 Native Desktop App Launcher
└── README.md                       # Windows 11 Documentation
```

---

## 💻 How to Launch Luna AI on Windows 11

After running `install.ps1` or `install_win11.bat`:

1. **Desktop / Start Menu**: Double-click **Luna AI**.
2. **Command Prompt / PowerShell**:
   ```cmd
   luna-ai
   :: or short command:
   luna
   :: or CLI mode:
   luna-cli
   ```

---

## 📜 License

Distributed under the **MIT License**.
