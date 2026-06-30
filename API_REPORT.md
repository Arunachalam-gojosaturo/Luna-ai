# LUNA OS X - API Report

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
