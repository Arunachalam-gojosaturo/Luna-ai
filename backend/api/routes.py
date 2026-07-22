import datetime
import os
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from backend.core.brain import LunaBrain
from backend.voice.tts import generate_tts
from backend.voice.stt import transcribe_audio, transcribe_local_audio
from backend.agents.linux_agent import LinuxAgent
from backend.api.agents import router as agents_router
from backend.memory.chat_history import chat_history_db

router = APIRouter()
router.include_router(agents_router)
brain = LunaBrain()
system_agent = LinuxAgent()

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "geminiEnabled": bool(os.getenv("GEMINI_API_KEY")),
        "timestamp": datetime.datetime.now().isoformat()
    }

class CommandRequest(BaseModel):
    command: str
    activeView: str = ""
    deviceStates: list = []
    history: list = []
    groqKey: str = ""
    geminiKey: str = ""
    openRouterKey: str = ""
    githubToken: str = ""
    nvidiaKey: str = ""
    cerebrasKey: str = ""
    bazaarlinkKey: str = ""
    togetherKey: str = ""
    cohereKey: str = ""
    openaiKey: str = ""
    modelSelection: str = ""
    activeProvider: str = "groq"
    isLocalLlm: bool = False
    localLlmUrl: str = ""
    localLlmModel: str = ""
    openClawApiKey: str = ""
    openClawUrl: str = ""


@router.post("/luna/command")
async def luna_command(req: CommandRequest):
    return await brain.process_request_json(req)

@router.get("/history")
async def get_history(session_id: str = "default"):
    return chat_history_db.get_history(session_id)

@router.post("/history/clear")
async def clear_history(session_id: str = "default"):
    chat_history_db.clear_history(session_id)
    return {"status": "cleared"}

class ExecuteRequest(BaseModel):
    sysCommand: str
    category: str = "RAW_COMMAND"

@router.post("/luna/execute")
async def luna_execute(req: ExecuteRequest):
    return await system_agent.execute(req.sysCommand, req.category)

class TTSRequest(BaseModel):
    text: str
    provider: str = "edge"
    voiceId: str = ""
    elevenLabsApiKey: str = ""
    speed: float = 1.0
    pitch: float = 1.0

@router.post("/tts")
async def tts(req: TTSRequest):
    audio_data = await generate_tts(req)
    return Response(content=audio_data, media_type="audio/mpeg")

@router.post("/tts/play_local")
async def tts_play_local(req: TTSRequest):
    import asyncio, tempfile, os
    from backend.core.voice_agent import voice_agent
    
    audio_data = await generate_tts(req)
    voice_agent.set_speaking(True)
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_data)
            tmp_name = f.name
        
        def play_audio():
            import subprocess
            import shutil
            try:
                if shutil.which("mpv"):
                    subprocess.run(["mpv", "--no-terminal", tmp_name], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                elif shutil.which("ffplay"):
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_name], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                elif shutil.which("paplay"):
                    # paplay needs WAV, but we have MP3. Convert if pydub available, else fail
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(tmp_name, format="mp3")
                    wav_path = tmp_name.replace(".mp3", ".wav")
                    audio.export(wav_path, format="wav")
                    subprocess.run(["paplay", wav_path], check=True)
                    if os.path.exists(wav_path): os.remove(wav_path)
                else:
                    print("No suitable audio player found (mpv, ffplay, paplay).")
            except Exception as e:
                print(f"Playback failed: {e}")
            finally:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
                    
        await asyncio.to_thread(play_audio)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        voice_agent.set_speaking(False)

@router.post("/stt")
async def stt(audio: UploadFile = File(...)):
    text = await transcribe_audio(audio)
    return {"transcript": text}

@router.post("/stt/record_local")
async def stt_record_local():
    from backend.core.voice_agent import voice_agent
    voice_agent.set_speaking(True) # suspend background listening temporarily
    try:
        text = await transcribe_local_audio()
        return {"transcript": text}
    finally:
        voice_agent.set_speaking(False) # resume background listening

class TTSStatusRequest(BaseModel):
    speaking: bool

@router.post("/tts/status")
async def set_tts_status(req: TTSStatusRequest):
    from backend.core.voice_agent import voice_agent
    voice_agent.set_speaking(req.speaking)
    return {"status": "ok"}

class FolderActionRequest(BaseModel):
    path: str = ""

@router.post("/system/pick-folder")
async def pick_folder():
    """Opens a native Arch Linux GTK/Qt GUI folder picker dialog."""
    import asyncio, sys, os, shutil
    from pathlib import Path
    
    venv_python = sys.executable
    script = "from PyQt6.QtWidgets import QApplication, QFileDialog; app = QApplication([]); print(QFileDialog.getExistingDirectory(None, 'Select Project Folder', '/home/arunachalam'))"
    
    selected_path = ""
    try:
        proc = await asyncio.create_subprocess_exec(
            venv_python, "-c", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        out_str = stdout.decode().strip()
        if out_str and os.path.exists(out_str):
            selected_path = out_str
    except Exception as e:
        print(f"[PickFolder Subprocess Exception]: {e}")

    if selected_path:
        return {"status": "success", "path": selected_path}
    
    return {"status": "success", "path": os.path.expanduser("~")}

@router.post("/system/open-file-manager")
async def open_file_manager(req: FolderActionRequest):
    """Detects and opens the system file manager (Dolphin, Thunar, Nautilus, xdg-open)."""
    target_path = req.path.strip() or os.path.expanduser("~")
    import shutil, subprocess
    fm_bin = next((cmd for cmd in ["dolphin", "thunar", "nautilus", "xdg-open"] if shutil.which(cmd)), "xdg-open")
    try:
        subprocess.Popen([fm_bin, target_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "success", "message": f"Opened {target_path} in {fm_bin}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
