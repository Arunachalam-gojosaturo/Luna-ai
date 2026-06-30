import os
import uuid
import speech_recognition as sr
from pydub import AudioSegment
from fastapi import UploadFile

async def transcribe_audio(audio: UploadFile) -> str:
    tmp_in = f".stt-tmp-in-{uuid.uuid4().hex}.webm"
    tmp_out = f".stt-tmp-out-{uuid.uuid4().hex}.wav"
    try:
        with open(tmp_in, "wb") as f:
            f.write(await audio.read())
            
        # Convert to wav using pydub
        audio_seg = AudioSegment.from_file(tmp_in)
        audio_seg.export(tmp_out, format="wav")
        
        # Recognize
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_out) as source:
            audio_data = recognizer.record(source)
            # The prompt mentions using Groq Whisper. I will implement a fallback to Google if Groq is not available
            # Let's check for GROQ API key in env
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                import requests
                with open(tmp_out, "rb") as audio_file:
                    headers = {"Authorization": f"Bearer {groq_key}"}
                    files = {"file": ("audio.wav", audio_file, "audio/wav")}
                    data = {"model": "whisper-large-v3-turbo"}
                    res = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files, data=data)
                    if res.ok:
                        return res.json().get("text", "")
            
            # Fallback to local / google
            text = recognizer.recognize_google(audio_data)
        return text
    except Exception as e:
        print("Transcription error:", e)
        return ""
    finally:
        if os.path.exists(tmp_in): os.remove(tmp_in)
        if os.path.exists(tmp_out): os.remove(tmp_out)
