# Luna AI (Luna OS X) - Complete Project Guide

# Executive Summary & Luna AI Introduction

## 🌙 Luna AI (Luna OS X) — Comprehensive Project Overview

Luna AI (also known as Luna OS X) represents a next-generation autonomous AI operating system and desktop assistant specifically engineered for Linux environments, with specialized optimization for Arch Linux, Hyprland window manager, Wayland display protocol, and both GTK and Qt desktop frameworks.

Unlike conventional chat-based AI interfaces that operate within limited conversational boundaries, Luna AI functions as a comprehensive autonomous operating system controller and intelligent digital companion. It integrates real-time continuous voice recognition, local system execution capabilities, multi-agent orchestration capabilities, wireless Android device integration via ADB, WhatsApp automation capabilities, and intelligent multi-provider LLM routing intelligence.

## 🏗️ High-Level System Architecture

Luna OS X implements a sophisticated decoupled Client-Server & Multi-Agent Architecture organized into distinct layers:

### Presentation Layers
The system offers three distinct user interface options:
- **React 19 + Vite Web App** (with Tauri/Chrome WebEngine option) - Modern web interface
- **PyQt6 Native Desktop App** (Zero-Browser Chrome embedded) - Native desktop experience  
- **Enhanced CLI Interface** - Terminal-based power user interface

These presentation layers communicate with the core AI engine through well-defined APIs.

### FASTAPI Python AI Core
At the heart of Luna AI lies the FastAPI-powered Python AI Core, comprising:

- **LunaBrain / LunaBrainV2** - Central intelligence node processing inputs and generating structured actions
- **Intent Router & Adaptive Decision Engine** - Routes user intents to appropriate processing paths
- **Execution Planner** - Formulates execution strategies for complex multi-step operations
- **Multi-Provider LLM Router** - Intelligently routes requests across Groq, Gemini, OpenAI, Cerebras, Together AI, Cohere, and local Ollama providers

### Modular Agent Ecosystem
Specialized agents handle specific domains:
- **Voice Pipeline** - Audio capture, voice activity detection, speech-to-text (Groq Whisper), text-to-speech (Edge TTS), and audio playback
- **Modular Agent Ecosystem** - Linux/System, ADB/Android, WhatsApp, GitHub/Git, File, and Package Manager agents
- **Memory Engines** - Working memory, SQLite chat storage, semantic memory, and PGVector storage

### Core Component Deep Dive

#### 1. AI Reasoning Brain (LunaBrain / LunaBrainV2)
Located in `backend/core/brain.py` and `backend/core/brain_v2.py`, this central intelligence node:
- Receives and processes user input commands
- Constructs dynamic system prompts enriched with real-time Linux telemetry (CPU, RAM, working directory status)
- Accesses semantic memory banks for contextual awareness
- Generates structured JSON action plans for execution
- Implements self-correction mechanisms with exponential backoff retry logic for rate-limited LLM providers

#### 2. Intent Router & Adaptive Decision Engine
Located in `backend/core/decision_engine.py` and `backend/core/planner.py`, this engine implements three reasoning depths:
- **FAST Path**: Bypasses multi-agent overhead for simple conversational queries and instant status checks
- **NORMAL Path**: Handles standard single-step operations for system/media/file management tasks
- **DEEP Path**: Engages multi-agent planning for complex workflows like code refactoring, system maintenance, and automation workflows

#### 3. Modular Agent Ecosystem (`backend/agents/` directory)
Each agent specializes in a specific domain:

| Agent Module | Primary Responsibilities |
|--------------|--------------------------|
| **Linux System Agent** (`linux_agent.py`, `system.py`) | Executes Arch Linux terminal commands, manages packages (pacman/yay/paru), controls system settings, manages Hyprland window manager via `hyprctl` |
| **Android ADB Agent** (`adb_manager.py`, `api/agents.py`) | Discovers Android devices via USB/local network, establishes wireless ADB connections, controls touch inputs (tap, swipe, text input), manages device lock/unlock via PIN, initiates screen mirroring via `scrcpy` |
| **WhatsApp Agent** (`whatsapp_agent.py`) | Automates headless WhatsApp Web for message sending and incoming chat monitoring |
| **GitHub & Git Agents** (`github_agent.py`, `git_agent.py`) | Analyzes repositories, retrieves user profile data, checks git status, commits code changes, pushes updates via GitHub REST API and local git CLI |
| **File Agent** (`file_agent.py`) | Handles file/directory operations, provides native GTK/Qt directory picker dialogs (via zenity, kdialog, PyQt6, tkinter), views file contents |
| **Package Manager Agent** (`package_manager.py`) | Manages system dependencies and installation workflows throughpackage managers |

#### 4. Voice Engine & Media Streaming
- **Continuous Voice Processing**: Managed by `backend/core/voice_agent.py` handling audio recording and Voice Activity Detection (VAD)
- **Media Streaming**: HTTP 206 Range support in `backend/api/routes.py` (`/api/system/media` endpoint) enables efficient HTML5 video playback, image thumbnail generation, and external player triggering (mpv, vlc)

#### 5. Enhanced CLI (`luna_cli_enhanced.py`)
Features include:
- ANSI color formatting and animated ASCII banners
- Command aliases and LLM provider profiles (groq, openai, google, openrouter)
- Real-time session statistics (uptime, success rate, command totals)
- WebSocket event listener for live task notifications

## 🛠️ Technology Stack Deep Dive

### Frontend & UI Technologies
- **Framework**: React 19 with TypeScript, Vite build tool, TailwindCSS v4 for styling
- **Animations**: Framer Motion (`motion`) for smooth transitions and micro-interactions
- **Icons**: Lucide React (`lucide-react`) for consistent, lightweight icons
- **Desktop Packaging**: 
  - Tauri v2 (Rust-backed) for secure, lightweight web-to-desktop wrapping
  - Native PyQt6 with QWebEngineView (Chromium embedded) for zero-browser Chrome experience

### Backend Core (Python 3.14+)
- **API Framework**: FastAPI for high-performance async APIs, Uvicorn as ASGI server
- **Real-time Communication**: WebSocket support for live updates
- **HTTP Client**: `httpx` (async) and `requests` (sync) for external API communication
- **System Control**: `psutil` for system monitoring, `subprocess`/`shutil`/`platform`/`asyncio` for system operations
- **Data Persistence**: 
  - SQLite3 (via `better-sqlite3` or standard `sqlite3`) for chat history and lightweight storage
  - SQLAlchemy with `asyncpg` for PostgreSQL + PGVector support (semantic search and embeddings)

### AI & Voice Engineering
- **LLM Routing**: Intelligent routing across providers:
  - Groq (Llama 3 models, Whisper for STT)
  - Google Gemini 2.0/2.5 Flash
  - OpenAI GPT-4o and other OpenAI models
  - Cerebras, Together AI, Cohere for alternative options
  - Local Ollama for private, on-premises model execution
- **Speech-to-Text**: 
  - Primary: Groq Whisper (`whisper-large-v3-turbo`) for high-speed, accurate transcription
  - Fallback: Google Speech Recognition API
- **Text-to-Speech**:
  - Primary: Microsoft Edge TTS (`node-edge-tts`/`edge-tts`) for natural-sounding synthesis
  - Fallbacks: ElevenLabs, PyTTSx3, gTTS for varied voice options
- **Media Playback**: Integration with `mpv`, `ffplay`, `paplay`, and `playerctl` for flexible audio/video handling

## 🎯 Skills & Domain Expertise Utilized

Building Luna AI required deep expertise across multiple domains:

### 1. System & OS Automation (Arch Linux / Wayland / Hyprland)
- Developed non-blocking asyncio subprocess runners for reliable command execution
- Implemented comprehensive security sandboxing and command whitelisting to prevent injection attacks
- Created privilege escalation handling mechanisms using `pkexec` dialogs for administrative tasks
- Developed Hyprland-specific window management via `hyprctl` commands
- Implemented Wayland-compatible screen recording and input simulation

### 2. Async Python Architecture & FastAPI Design
- Architected high-concurrency ASGI route handling for maximum throughput
- Implemented WebSocket connections for real-time bidirectional communication
- Designed modular dependency injection and singleton lifecycle management for service components
- Created structured error handling and graceful degradation patterns

### 3. Multi-Model LLM Orchestration & Failover
- Implemented exponential backoff strategies for rate limit mitigation across all LLM providers
- Engineered structured JSON response enforcement through prompt engineering and output validation
- Developed dynamic system context injection that includes real-time system telemetry
- Created intelligent fallback chains between LLM providers based on availability, cost, and performance

### 4. Hardware & Mobile Control (Android ADB Bridge)
- Built wireless ADB device discovery through local network scanning
- Implemented TCP/IP socket negotiation for reliable ADB connections over WiFi
- Created automated device unlocking mechanisms using Android key-event simulation
- Developed direct integration with `scrcpy` for seamless screen mirroring
- Implemented USB device monitoring for automatic detection when devices are connected

### 5. Audio Signal & Voice Pipeline Engineering
- Developed low-latency Voice Activity Detection (VAD) using energy-based and spectral methods
- Implemented circular audio buffer management for continuous audio processing
- Integrated Edge TTS synthesis with subprocess audio routing to multiple output systems
- Created audio mixing capabilities for simultaneous TTS playback and system sounds
- Implemented audio device selection and routing for multi-input/multi-output scenarios

### 6. Modern Frontend & Cross-Platform Desktop Packaging
- Implemented React 19 functional components with hooks for state management
- Created real-time telemetry dashboards using WebSocket connections to backend
- Built zero-chrome desktop applications using Tauri's security-first approach
- Developed PyQt6 applications with QWebEngineView for Chromium embedding with custom protocols
- Implemented cross-platform packaging scripts for Linux distributions

## ⚡ Project Execution Commands

### Development & Testing
```bash
# Start the web/backend server (FastAPI on http://127.0.0.1:3000)
npm run start

# Launch the Vite web frontend development server (http://127.0.0.1:5173)
npm run dev

# Launch the native PyQt6 desktop application
npm run app

# Start the enhanced terminal-based CLI interface
npm run cli

# Run TypeScript type checking (no emission)
npm run lint

# Create production-optimized build
npm run build
```

### Development Workflow
1. **Backend Development**: Modify Python files in `backend/` directory, then restart with `npm run start`
2. **Frontend Development**: Edit React components in `frontend/` directory, changes hot-reload with `npm run dev`
3. **Desktop App Testing**: Use `npm run app` to test native desktop functionality
4. **CLI Testing**: Use `npm run cli` for terminal-based interactions and debugging
5. **Type Safety**: Run `npm run lint` regularly during development to catch TypeScript errors

### Production Deployment
1. Build production assets: `npm run build`
2. Deploy built assets to your preferred hosting/service
3. For desktop distribution, use Tauri/PyQt6 packaging tools to create platform-specific installers
4. Set up environment variables for API keys (Groq, Gemini, etc.) in production environment

## 📖 How to Use This Guide

This guide is structured to serve multiple audiences:

### For New Contributors
1. Start with the **Executive Summary** to understand Luna AI's vision and scope
2. Review the **High-Level System Architecture** to grasp the overall system design
3. Explore the **Technology Stack** section to understand the tools and technologies used
4. Dive into **Deep Dive into Core Components** for detailed implementation insights
5. Refer to **Skills & Mastery Utilized** to understand the expertise domains involved
6. Use **Project Execution Commands** for getting started with development

### For Developers
- Use the **Technology Stack** and **Deep Dive** sections as implementation references
- Consult **Skills & Mastery Utilized** when tackling specific domain challenges
- Follow the **Project Execution Commands** for development workflows
- Reference the component-specific details when modifying or extending functionality

### For Users & Administrators
- Focus on the **Executive Summary** for operational understanding

## 📚 Next Steps

This guide provides a complete picture. For detailed implementation reference the component-specific directories
- Refer to **Executive Summary** and **High-Level System Architecture** for capability overview
- Use **Project Execution Commands** for installation and operation guidance
- Consult specific component sections for advanced configuration and troubleshooting

---

*This document serves as a living reference for the Luna AI (Luna OS X) project. As the system evolves, this guide should be updated to reflect new features, architectural changes, and usage patterns.*