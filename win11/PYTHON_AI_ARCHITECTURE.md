# LUNA OS X - Python AI Architecture

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
