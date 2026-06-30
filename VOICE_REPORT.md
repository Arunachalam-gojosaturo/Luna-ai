# LUNA OS X - Voice Engine Report

## Architecture
1. **Input**: Blob audio via `UploadFile` to `/api/stt`.
2. **VAD / STT**: Processed through Groq's `whisper-large-v3-turbo` for ultra-low latency transcription. Fallback to Google STT.
3. **Response**: AI Brain generates text and required actions.
4. **Output**: Text is sent to `/api/tts` which streams Edge TTS (or ElevenLabs) back to the client as an MP3.

## Characteristics
* Async processing.
* Local temporary file cleanup (`.wav`, `.webm`).
* Multi-provider TTS fallback.
