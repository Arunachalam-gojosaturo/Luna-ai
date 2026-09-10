import os
import uuid
import re
import edge_tts
import httpx

def apply_arunachalam_pronunciation(text: str) -> str:
    """
    ARUNACHALAM NAME PRONUNCIATION PROTOCOL
    
    When Luna speaks Arunachalam's name using Text-to-Speech (Edge TTS / ElevenLabs),
    the name is pronounced phonetically as 'Aru-naa-cha-lam'.
    
    Automatically detects variations:
    - Arunachalam
    - ARUNACHALAM
    - Arunachalam's
    - Arunachalam.
    
    Replaces them internally strictly for speech generation without altering
    written text in the UI, chat history, logs, or memory.
    """
    if not text:
        return ""
    # Possessive: Arunachalam's / ARUNACHALAM'S -> Aru-naa-cha-lam's
    formatted = re.sub(r"\bArunachalam('s|\u2019s)\b", r"Aru-naa-cha-lam\1", text, flags=re.IGNORECASE)
    # Base name with word boundary
    formatted = re.sub(r"\bArunachalam\b", "Aru-naa-cha-lam", formatted, flags=re.IGNORECASE)
    return formatted

import asyncio
import io
import soundfile as sf

_kokoro_instance = None

def get_kokoro():
    global _kokoro_instance
    if _kokoro_instance is not None:
        return _kokoro_instance

    candidate_model_dirs = [
        os.getenv("KOKORO_MODELS_DIR", ""),
        os.path.expanduser("~/.local/share/luna-ai/models"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models"),
        "/home/arunachalam/testtts",
    ]

    model_path = os.getenv("KOKORO_MODEL_PATH", "")
    voices_path = os.getenv("KOKORO_VOICES_PATH", "")

    if not (model_path and os.path.exists(model_path)):
        for d in candidate_model_dirs:
            if d and os.path.isdir(d):
                p = os.path.join(d, "kokoro-v1.0.onnx")
                if os.path.exists(p):
                    model_path = p
                    break

    if not (voices_path and os.path.exists(voices_path)):
        for d in candidate_model_dirs:
            if d and os.path.isdir(d):
                p = os.path.join(d, "voices-v1.0.bin")
                if os.path.exists(p):
                    voices_path = p
                    break

    if model_path and voices_path and os.path.exists(model_path) and os.path.exists(voices_path):
        try:
            from kokoro_onnx import Kokoro
            _kokoro_instance = Kokoro(model_path, voices_path)
            print(f"[TTS] Kokoro-ONNX Offline TTS Engine initialized ({model_path}).")
        except Exception as e:
            print(f"[TTS] Failed to initialize Kokoro-ONNX: {e}")

    return _kokoro_instance

def generate_kokoro_tts_bytes(text: str, voice: str = "af_bella", speed: float = 1.0) -> bytes:
    kokoro = get_kokoro()
    if not kokoro:
        raise RuntimeError("Kokoro-ONNX model files (kokoro-v1.0.onnx, voices-v1.0.bin) not found. Please install them to ~/.local/share/luna-ai/models or /home/arunachalam/testtts")
    samples, sample_rate = kokoro.create(text, voice=voice or "af_bella", speed=speed, lang="en-us")
    buf = io.BytesIO()
    sf.write(buf, samples, sample_rate, format="WAV")
    return buf.getvalue()

async def generate_tts(req) -> bytes:
    tts_text = apply_arunachalam_pronunciation(req.text)
    provider = getattr(req, "provider", "edge").lower()

    # 1. Explicit Kokoro / Offline TTS requested
    if provider in ["kokoro", "offline"]:
        return await asyncio.to_thread(generate_kokoro_tts_bytes, tts_text, req.voiceId or "af_bella", req.speed)

    # 2. ElevenLabs
    if provider == "elevenlabs" and getattr(req, "elevenLabsApiKey", None):
        try:
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": req.elevenLabsApiKey
            }
            data = {
                "text": tts_text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{req.voiceId or 'EXAVITQu4vr4xnSDxMaL'}",
                    headers=headers,
                    json=data
                )
                if not res.is_success:
                    raise ValueError(f"ElevenLabs API error: {res.status_code} - {res.text}")
                return res.content
        except Exception as el_err:
            print(f"[TTS] ElevenLabs failed: {el_err}, attempting fallback...")

    # 3. Default Online Edge-TTS with Auto-Switch to Kokoro-ONNX Offline
    tmp_file = f"/tmp/.tts-tmp-{uuid.uuid4().hex}.mp3"
    try:
        voice = req.voiceId or "en-US-AriaNeural"
        rate_str = f"+{int((req.speed - 1)*100)}%" if req.speed > 1 else f"{int((req.speed - 1)*100)}%" if req.speed != 1.0 else "+0%"
        pitch_str = f"+{int((req.pitch - 1)*50)}Hz" if req.pitch > 1 else f"{int((req.pitch - 1)*50)}Hz" if req.pitch != 1.0 else "+0Hz"
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                try:
                    communicate = edge_tts.Communicate(tts_text, voice, rate=rate_str, pitch=pitch_str)
                except ValueError:
                    voice = "en-US-AriaNeural"
                    communicate = edge_tts.Communicate(tts_text, voice, rate=rate_str, pitch=pitch_str)
                await communicate.save(tmp_file)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(0.5)
        
        with open(tmp_file, "rb") as f:
            audio_data = f.read()
        return audio_data
    except Exception as edge_err:
        print(f"[TTS] Online Edge-TTS unavailable ({edge_err}). Auto-switching to Offline Kokoro-ONNX TTS...")
        try:
            return await asyncio.to_thread(generate_kokoro_tts_bytes, tts_text, "af_bella", req.speed)
        except Exception as kokoro_err:
            raise ValueError(f"TTS generation failed (Edge-TTS: {edge_err} | Kokoro-ONNX: {kokoro_err})")
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
