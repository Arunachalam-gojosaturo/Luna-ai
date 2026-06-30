import os
import uuid
import edge_tts
import requests

async def generate_tts(req) -> bytes:
    tmp_file = f".tts-tmp-{uuid.uuid4().hex}.mp3"
    try:
        if req.provider == "elevenlabs" and req.elevenLabsApiKey:
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": req.elevenLabsApiKey
            }
            data = {
                "text": req.text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
            }
            res = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{req.voiceId or 'EXAVITQu4vr4xnSDxMaL'}", headers=headers, json=data)
            return res.content
        else:
            voice = req.voiceId or "en-US-AriaNeural"
            rate_str = f"+{int((req.speed - 1)*100)}%" if req.speed > 1 else f"{int((req.speed - 1)*100)}%" if req.speed != 1.0 else "+0%"
            pitch_str = f"+{int((req.pitch - 1)*50)}Hz" if req.pitch > 1 else f"{int((req.pitch - 1)*50)}Hz" if req.pitch != 1.0 else "+0Hz"
            
            try:
                communicate = edge_tts.Communicate(req.text, voice, rate=rate_str, pitch=pitch_str)
            except ValueError:
                voice = "en-US-AriaNeural"
                communicate = edge_tts.Communicate(req.text, voice, rate=rate_str, pitch=pitch_str)
            await communicate.save(tmp_file)
            
            with open(tmp_file, "rb") as f:
                audio_data = f.read()
            return audio_data
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
