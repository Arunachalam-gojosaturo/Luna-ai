import os
import uuid
import speech_recognition as sr
from pydub import AudioSegment
from fastapi import UploadFile
import httpx

async def transcribe_audio(audio: UploadFile) -> str:
    tmp_in = f"/tmp/.stt-tmp-in-{uuid.uuid4().hex}.webm"
    tmp_out = f"/tmp/.stt-tmp-out-{uuid.uuid4().hex}.wav"
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
            # Check for Groq Whisper support
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    with open(tmp_out, "rb") as audio_file:
                        headers = {"Authorization": f"Bearer {groq_key}"}
                        files = {"file": ("audio.wav", audio_file, "audio/wav")}
                        data = {"model": "whisper-large-v3-turbo"}
                        try:
                            res = await client.post(
                                "https://api.groq.com/openai/v1/audio/transcriptions",
                                headers=headers,
                                files=files,
                                data=data
                            )
                            if res.status_code == 200:
                                transcript = res.json().get("text", "").strip()
                                if transcript:
                                    return transcript
                                else:
                                    print("Groq returned empty transcript, falling back to Google")
                            else:
                                print(f"Groq API returned status {res.status_code}: {res.text}")
                        except Exception as e:
                            print(f"Groq transcription error: {e}")
            
            # Fallback to Google Speech Recognition
            try:
                text = recognizer.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return "Could not understand the audio"
            except sr.RequestError as e:
                return f"Google Speech Recognition error: {e}"
    except Exception as e:
        print("Transcription error:", e)
        return "Error: Could not process audio."
    finally:
        if os.path.exists(tmp_in): os.remove(tmp_in)
        if os.path.exists(tmp_out): os.remove(tmp_out)

async def transcribe_local_audio() -> str:
    import uuid
    import asyncio
    tmp_out = f"/tmp/.stt-tmp-out-{uuid.uuid4().hex}.wav"
    try:
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                print("🎤 Listening for local STT...")
                # Run the blocking listen in a thread
                audio_data = await asyncio.to_thread(recognizer.listen, source, timeout=10, phrase_time_limit=15)
        except sr.WaitTimeoutError:
            print("Listening timed out (no speech detected).")
            return ""
        except (OSError, RuntimeError) as e:
            error_msg = str(e).lower()
            if "permission" in error_msg or "cannot connect" in error_msg or "device" in error_msg:
                print("❌ Microphone access error. Fix: sudo usermod -aG audio $(whoami) && newgrp audio")
                return "Microphone access denied. Please grant audio permissions and restart Luna."
            raise
            
        with open(tmp_out, "wb") as f:
            f.write(audio_data.get_wav_data())

        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(tmp_out, "rb") as audio_file:
                    headers = {"Authorization": f"Bearer {groq_key}"}
                    files = {"file": ("audio.wav", audio_file, "audio/wav")}
                    data = {"model": "whisper-large-v3-turbo"}
                    try:
                        res = await client.post(
                            "https://api.groq.com/openai/v1/audio/transcriptions",
                            headers=headers,
                            files=files,
                            data=data
                        )
                        if res.status_code == 200:
                            transcript = res.json().get("text", "").strip()
                            if transcript:
                                return transcript
                    except Exception as e:
                        print(f"Groq transcription error: {e}")
        
        # Fallback to Google Speech Recognition
        try:
            text = await asyncio.to_thread(recognizer.recognize_google, audio_data)
            return text
        except sr.UnknownValueError:
            return "Could not understand the audio"
        except sr.RequestError as e:
            return f"Google Speech Recognition error: {e}"
    except Exception as e:
        error_msg = str(e).lower()
        if "permission" in error_msg or "input" in error_msg:
            print("❌ Local Transcription - Microphone Permission Error:", e)
            print("   Fix: sudo usermod -aG audio $(whoami) && newgrp audio")
            return "Microphone permission denied. Run: sudo usermod -aG audio $(whoami)"
        else:
            print("❌ Local Transcription error:", e)
            return "Error: Could not access microphone. Check permissions."
    finally:
        if os.path.exists(tmp_out): os.remove(tmp_out)

