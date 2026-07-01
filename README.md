# 🌙 Luna Ecosystem (Luna OS X)

<div align="center">
  <img src="public/background.png" alt="Luna OS X" width="100%" />
</div>

<div align="center">
  <strong>An AI-powered Operating System Ecosystem for Arch Linux</strong>
</div>

<br />

<div align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#project-structure">Structure</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a>
</div>

## 🌌 Overview

**Luna OS X** is an AI-powered operating system layer designed specifically for Arch Linux. It features a Python-based AI brain, real-time voice interaction, long-term memory, intelligent Linux automation, and developer tools. It combines a modern desktop UI with a powerful assistant that can manage projects, control the system, and automate everyday tasks.

---

## ✨ Key Features

- 🧠 **AI Brain**: Powered by state-of-the-art LLMs, orchestrating multiple specialized agents.
- 🗣️ **Real-Time Voice Interaction**: Seamless Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities.
- 🗄️ **Long-Term Memory**: Utilizes ChromaDB for semantic memory and SQLite for chat history, ensuring Luna remembers past interactions and context.
- 🐧 **Linux Automation**: Deep integration with Linux. Agents can run commands, manage packages, and handle files.
- 💻 **Developer Workspace**: Built-in developer tools and Git agents to assist with coding and repository management.
- 🎨 **Modern UI**: A beautiful, fluid interface built with React, Tailwind CSS, and Framer Motion, packaged as a lightweight desktop app via **Tauri**.

---

## 🏗️ Architecture & Tech Stack

### Frontend (Desktop App)
- **Framework**: React 19 + TypeScript
- **Styling**: Tailwind CSS + Motion (Framer)
- **Desktop Runtime**: Tauri (Rust)
- **Build Tool**: Vite

### Backend (AI Brain)
- **Framework**: FastAPI (Python)
- **Memory**: ChromaDB (Vector Database) + SQLite
- **Voice**: Edge TTS
- **AI Core**: Modular architecture with Decision Engine, Planner, Executor, and Context Engine.

---

## 📂 Full Project Structure

```text
Luna-eco-system/
├── backend/                  # Python FastAPI Backend & AI Logic
│   ├── agents/               # Specialized AI Agents (Git, Linux, File, Package)
│   ├── api/                  # REST and WebSocket API Routes
│   ├── core/                 # Core AI logic (Brain, Planner, Orchestrator, Context)
│   ├── memory/               # Memory Management (ChromaDB, SQLite, Summarizer)
│   ├── providers/            # LLM Provider Integrations
│   ├── tools/                # Tool Registries for Agents
│   └── voice/                # STT and TTS engines
├── src/                      # React Frontend Source
│   ├── components/           # UI Components (DeveloperWorkspace, Settings, etc.)
│   ├── App.tsx               # Main React Application
│   └── index.css             # Tailwind CSS entry
├── src-tauri/                # Tauri Rust Backend (Desktop Shell)
│   ├── src/                  # Rust source code
│   └── tauri.conf.json       # Tauri configuration
├── dist/                     # Compiled Frontend build
├── public/                   # Static Assets
├── package.json              # Node.js dependencies & scripts
├── requirements.txt          # Python dependencies
├── server.py                 # Backend Entry Point
├── cli.py                    # Legacy Command Line Interface
├── luna_cli_enhanced.py      # Enhanced CLI with animations
├── cli_utils.py              # CLI utilities & UI components
├── cli_config.py             # CLI configuration management
├── cli_examples.py           # CLI feature demonstrations
├── CLI_GUIDE.md              # Complete CLI documentation
├── CLI_QUICKSTART.md         # Quick start guide
└── LUNA_CLI_ENHANCEMENTS.md  # Enhancement summary
```

---

## 🚀 Installation

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- Rust & Cargo (for Tauri)
- Arch Linux (recommended for full system integration)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Arunachalam-gojosaturo/Luna-eco-system.git
   cd Luna-eco-system
   ```

2. **Install Frontend Dependencies:**
   ```bash
   npm install
   ```

3. **Set up Python Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Rename `.env.example` to `.env` and add your API keys:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

---

## 💻 Usage

### Run Locally (Development)
You can start both the backend FastAPI server and the Vite frontend simultaneously with:
```bash
npm run dev
```

### Run Enhanced CLI
Start the beautiful enhanced Luna CLI with awesome boot animations:
```bash
npm run cli
```

Or directly:
```bash
python luna_cli_enhanced.py
```

### Run CLI Demo
Test all CLI features with comprehensive demo:
```bash
npm run cli:test
```

### Run Desktop App
To run the project as a native desktop application using Tauri:
```bash
npm run desktop
```

### Build Desktop App
To compile a production-ready binary for your system:
```bash
npm run desktop:build
```

---

## 🎯 CLI Features

The enhanced Luna CLI includes:

- **🎨 Awesome Boot Animation** - Colorized ASCII art with animated startup
- **🎯 Attribute-Based Commands** - Commands as objects with metadata
- **💬 8 Core Commands** - help, status, history, clear, model, voice, memory, exit
- **📊 Rich UI Components** - Progress bars, spinners, tables, status indicators
- **⚙️ Configuration System** - Profiles, aliases, history management
- **🔧 Complete Documentation** - Guides and examples included

**Quick Start:**
```bash
npm run cli
luna> help      # Show all commands
luna> status    # Display statistics
luna> exit      # Exit gracefully
```

See [CLI_QUICKSTART.md](CLI_QUICKSTART.md) for detailed guide.

---

## 🛡️ License

This project is licensed under the MIT License.

---
*Created by [Arunachalam](https://github.com/Arunachalam-gojosaturo)*
