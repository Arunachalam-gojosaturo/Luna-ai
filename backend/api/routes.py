import datetime
import os
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from backend.core.brain import LunaBrain
from backend.voice.tts import generate_tts
from backend.voice.stt import transcribe_audio
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
    openRouterKey: str = ""
    openaiKey: str = ""
    modelSelection: str = ""
    activeProvider: str = "groq"

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

@router.post("/stt")
async def stt(audio: UploadFile = File(...)):
    text = await transcribe_audio(audio)
    return {"transcript": text}
