import os

PYTHON_AI_ARCHITECTURE = """# LUNA OS X - Python AI Architecture

## Overview
LUNA OS X has been migrated to a fully localized Python AI Core. The React frontend is now purely a presentation layer, completely devoid of AI reasoning. All logic, memory, tool orchestration, and voice pipelines live securely within the FastAPI backend.

## Components
1. **AI Brain (`backend/core/brain.py`)**: Central reasoning engine, prompt builder, and tool selector.
2. **Provider Manager (`backend/core/provider.py`)**: Seamlessly routes requests between Groq, OpenRouter, Gemini, and OpenAI.
3. **Agent Ecosystem (`backend/agents/`)**: Individual, modular Python agents with their own APIs.
4. **Memory Engine (`backend/memory/db.py`)**: PostgreSQL-backed vector database for infinite, semantic recall.
5. **Voice Pipeline (`backend/voice/`)**: Real-time microphone capture -> VAD -> Groq Whisper STT -> Edge TTS.

## Flow
React UI -> `POST /api/luna/command` -> `LunaBrain` -> `ProviderManager` -> (LLM Inference) -> `Agent API` -> `System Execution` -> Response JSON -> React UI
"""

AGENT_REPORT = """# LUNA OS X - Agent System Report

## Deployed Agents
All agents are deployed as modular microservices within the FastAPI router namespace `/api/agents/*`.

* **System Agent (`/api/luna/execute`)**: Connects to Arch Linux root processes using `asyncio.subprocess`. Safely executes sys-commands and monitors system telemetry using `psutil`.
* **Browser Agent (`/api/agents/browser`)**: Handles internet research, HTML DOM extraction, and URL navigation.
* **File Agent (`/api/agents/file`)**: Reads, writes, modifies, and indexes the local file system.
* **Terminal Agent (`/api/agents/terminal`)**: Sandboxed CLI execution environment.
* **GitHub Agent**: Manages `git` processes and source control workflows.
* **Device Agent**: Cross-platform telemetry ingestion.

## Function Calling
The AI Brain autonomously invokes these agents based on contextual intent.
"""

API_REPORT = """# LUNA OS X - API Report

## Endpoints

### Core endpoints
* `GET /api/health` - Check backend status and active providers.
* `POST /api/luna/command` - Primary LLM interaction loop. Returns structured state and commands.
* `POST /api/luna/execute` - Arch Linux direct command execution (requires pkexec if privileged).

### Voice endpoints
* `POST /api/tts` - Edge TTS and ElevenLabs audio generation.
* `POST /api/stt` - Groq Whisper and fallback Google Speech-To-Text.

### Agent endpoints
* `POST /api/agents/browser`
* `POST /api/agents/file`
* `POST /api/agents/terminal`
"""

MEMORY_REPORT = """# LUNA OS X - Memory Engine Report

## PostgreSQL & PGVector Migration
SQLite has been deprecated in favor of a robust async PostgreSQL pipeline using SQLAlchemy.

### Features
* **Semantic Search**: Every conversation turn is embedded and stored.
* **Async Engine**: Uses `asyncpg` for non-blocking database queries.
* **Data Models**: 
  - `Conversation`: Persistent logs of all user/assistant interactions.
  - `SystemGoal`: Dynamic tracking of background tasks and long-term objectives.

*(Note: Requires PostgreSQL instance running locally with pgvector extension).*
"""

VOICE_REPORT = """# LUNA OS X - Voice Engine Report

## Architecture
1. **Input**: Blob audio via `UploadFile` to `/api/stt`.
2. **VAD / STT**: Processed through Groq's `whisper-large-v3-turbo` for ultra-low latency transcription. Fallback to Google STT.
3. **Response**: AI Brain generates text and required actions.
4. **Output**: Text is sent to `/api/tts` which streams Edge TTS (or ElevenLabs) back to the client as an MP3.

## Characteristics
* Async processing.
* Local temporary file cleanup (`.wav`, `.webm`).
* Multi-provider TTS fallback.
"""

FINAL_BACKEND_REPORT = """# LUNA OS X - Final Backend Migration Report

## Status: COMPLETE

The transition of all LUNA OS X intelligence to the Python AI Core is complete. 
The React frontend (in `src/App.tsx`) continues to operate identically in terms of visuals, but all logic—including conversation history management, system command validation, LLM routing, and tool dispatch—has been replicated and expanded in the new Python `backend/` directory.

### Key Achievements
1. **Zero UI modifications**: Visuals remain pristine.
2. **Modular Architecture**: Built on FastAPI with strict separation of concerns (Core, API, Voice, Agents, Memory).
3. **Robust Provider Fallback**: OpenRouter -> Groq -> Gemini -> OpenAI -> Local Fallback.
4. **Enhanced Security**: Arch Linux command validation occurs server-side with strict audit logging.

The system is now a true AI Operating System backend, ready for scalable local AI integration.
"""

files = {
    "PYTHON_AI_ARCHITECTURE.md": PYTHON_AI_ARCHITECTURE,
    "AGENT_REPORT.md": AGENT_REPORT,
    "API_REPORT.md": API_REPORT,
    "MEMORY_REPORT.md": MEMORY_REPORT,
    "VOICE_REPORT.md": VOICE_REPORT,
    "FINAL_BACKEND_REPORT.md": FINAL_BACKEND_REPORT
}

for name, content in files.items():
    with open(name, "w") as f:
        f.write(content)

print("Generated all reports successfully.")
