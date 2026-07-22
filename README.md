<div align="center">
  <img src="assets/luna-ai.png" alt="Luna OS Header" width="100%" />
  <br/>
  <br/>
  <img src="assets/luna-logo.png" alt="Luna OS Logo" width="128" />
  <p><strong>A Next-Generation Voice-Activated Desktop AI Assistant for Linux</strong></p>
  
  [![Tauri](https://img.shields.io/badge/Built_with-Tauri-blue?logo=tauri)](https://tauri.app/)
  [![React](https://img.shields.io/badge/Frontend-React_18-61dafb?logo=react)](https://reactjs.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Linux](https://img.shields.io/badge/Platform-Arch_Linux-1793d1?logo=arch-linux)](https://archlinux.org/)
</div>

<hr/>

## 🌌 What is Luna?
**Luna AI** is a powerful, autonomous desktop assistant designed to deeply integrate with your Linux environment. Unlike standard chatbots, Luna is built as a native **Tauri desktop application** with a **FastAPI Python backend**, giving her the ability to directly control your operating system.

Whether you want to launch applications, switch workspaces, control your media, manage files, or just have a voice conversation, Luna can handle it seamlessly.

## ✨ Features
* 🎙️ **Always-On Voice Recognition:** Talk to Luna without clicking. Features continuous listening with automatic silence detection (powered by Groq Whisper & Google STT).
* 🗣️ **Native Voice Responses:** Luna replies back with fast Text-to-Speech (TTS), dynamically playing audio through your system.
* 🖥️ **Deep System Integration:**
  * **App Control:** "Open Firefox", "Close Discord".
  * **Workspace Management:** "Switch to workspace 2" (Hyprland / Wayland support).
  * **Media & Audio:** Control volume and media playback natively.
  * **File Operations:** Move, copy, and read files via natural language.
* 🛡️ **Secure Execution:** Elevated commands are intercepted and prompt a visual `pkexec` authorization window before executing. No silent `sudo` risks.
* ⚡ **Lightning Fast UI:** Built on Tauri + React + Vite. Uses less RAM than Electron and feels incredibly responsive.

## 🛠️ Tech Stack
* **Frontend:** React, TypeScript, Vite, TailwindCSS
* **Desktop Framework:** Tauri (Rust)
* **Backend Core:** Python 3, FastAPI, Uvicorn
* **AI & Voice Engine:** Groq API (Whisper v3), Google Speech Recognition, gTTS, OpenAI LLM routing.
* **System Utilities:** `mpv`, `hyprctl`, `xdg-open`, `pkexec`

## 🚀 Installation & Setup

### ⚡ Option A: Universal One-Line Installer (All Linux Distros)
Supports **Arch Linux, Ubuntu, Debian, Pop!_OS, Linux Mint, Fedora, RHEL, openSUSE, Alpine**.
Automatically detects your OS, installs system dependencies, builds web assets, and sets up launchers:

```bash
curl -sSL https://raw.githubusercontent.com/Arunachalam-gojosaturo/Luna-ai/main/install.sh | bash
```

---

### 📦 Option B: Arch Linux AUR (`yay` / `paru`)
If you are running Arch Linux or an Arch-based distribution:

```bash
yay -S luna-ai
# or
paru -S luna-ai
```

---

### 🛠️ Option C: Manual Installation
```bash
git clone https://github.com/Arunachalam-gojosaturo/Luna-ai.git
cd Luna-ai
./install.sh
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory and add your API keys:
```env
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
```

### 3. Build & Install
Run the provided installer script, which will automatically configure the Python virtual environment, compile the Tauri React app, and install the desktop shortcut.
```bash
npm install
npm run desktop:build
./install.sh
```

### 4. Launch Luna
You can now find **Luna OS** in your application launcher (Rofi/Wofi/Gnome) or start it from the terminal:
```bash
luna-os
```

## 🧠 Architecture Overview
* **Frontend App (`src/`):** Manages the graphical interface, manages the continuous microphone loop, and renders the chat view.
* **Tauri Core (`src-tauri/`):** Spawns the background Python server on port `3000` and creates the native system tray/window.
* **Python Backend (`backend/`):**
  * `api/routes.py`: Handles HTTP POST requests for `/luna/execute`, STT, and TTS.
  * `core/brain.py`: The "LLM Router" that processes transcripts and decides whether to chat, execute a system command, or throw an error.
  * `agents/linux_agent.py`: Safely executes bash commands and creates audit logs inside `~/.cache/luna-os/`.

## 🤝 Contributing
Feel free to fork the repository and submit pull requests. Ensure you test voice functionalities and system execution on a Linux machine (preferably Arch Linux) before submitting changes.

## 📜 License
MIT License. See `LICENSE` for more details.
