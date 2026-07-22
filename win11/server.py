import os
import sqlite3
import json
import asyncio
import uuid
import datetime
import tempfile
import subprocess
import requests
import psutil
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import speech_recognition as sr
from pydub import AudioSegment
import edge_tts
from google import genai
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "luna_memory.db"
AUDIT_LOG_PATH = "audit.log"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Init DB
def init_db():
    conn = get_db()
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversation_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            role TEXT,
            content TEXT,
            embedding BLOB
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS system_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def append_audit_log(command, intent, sys_command, privilege):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] INTENT: {intent} | PRIVILEGE: {privilege} | CMD: {command} | EXEC: {sys_command}\n"
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(log_entry)

def save_message(role, content):
    conn = get_db()
    conn.execute("INSERT INTO conversation_memory (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def get_recent_context(limit=10):
    conn = get_db()
    cur = conn.execute("SELECT role, content FROM conversation_memory ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

def validate_command(command: str):
    # Basic permission manager
    if "rm -rf /" in command:
        return {"allowed": False, "reason": "Destructive command"}
    # Strip sudo if provided, for safety we can just allow it since it's a personal AI
    return {"allowed": True, "wrappedCommand": command}

async def execute_system_command(command: str, category: str):
    append_audit_log(command, category, command, "sudo" in command)
    val = validate_command(command)
    if not val["allowed"]:
        return {"success": False, "stdout": "", "stderr": val["reason"]}
    
    try:
        proc = await asyncio.create_subprocess_shell(
            val["wrappedCommand"],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else ""
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "geminiEnabled": bool(os.getenv("GEMINI_API_KEY")),
        "timestamp": datetime.datetime.now().isoformat()
    }

class CommandRequest(BaseModel):
    command: str
    activeView: str = ""
    deviceStates: dict = {}
    history: list = []
    groqKey: str = ""
    openRouterKey: str = ""
    openaiKey: str = ""
    modelSelection: str = ""

@app.post("/api/luna/command")
async def luna_command(req: CommandRequest):
    command = req.command
    import platform
    os_name = platform.system()
    open_cmd = "start" if os_name == "Windows" else ("open" if os_name == "Darwin" else "xdg-open")

    system_prompt = f"""You are Luna, a highly intelligent, sophisticated personal AI Operating System (Version 3.0).
You control a {os_name} workstation.
When the user enters an input, analyze their request and respond in the following structured JSON format:
{{
  "state": "Idle" | "Listening" | "Thinking" | "Speaking" | "Executing" | "Warning",
  "speech": "Your response text to display and read out loud. Speak like a friendly personal assistant.",
  "action": "APP_CONTROL" | "SYSTEM_MANAGEMENT" | "FILE_OPERATION" | "MONITORING" | "SYNC_DEVICE" | "RUN_TESTS" | "TRIGGER_BUILD" | "ADD_GOAL" | "TOGGLE_DEVICE" | "EXECUTE_SYSTEM_COMMAND" | "GIT_AUTOMATION" | "NONE",
  "sysCommand": "The exact bash/shell command to execute. For URLs use '{open_cmd} <url>'. To play a song on YouTube, use '{open_cmd} \"https://music.youtube.com/search?q=SONG_NAME\"'. For GIT_AUTOMATION, use 'auto_commit' (to automatically diff and generate an AI commit) or 'auto_push', or normal git commands.",
  "requiresPrivilege": false,
  "targetDevice": "Android" | "Linux" | "Windows" | "NONE",
  "logs": ["Array of 4 to 6 lines of simulated highly technical logs"],
  "notifications": ["Array of short notifications"]
}}
Ensure the output is strictly valid JSON conforming exactly to the schema.
The user is viewing the "{req.activeView}" view. Devices: {json.dumps(req.deviceStates)}.
User command: "{command}"
"""
    recent_memory = get_recent_context(10)
    memory_str = "\\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent_memory])
    if memory_str:
        system_prompt += f"\\nRecent History:\\n{memory_str}"
        
    messages = [{"role": "system", "content": system_prompt}]
    for msg in req.history:
        r = "assistant" if msg.get("role") in ["model", "assistant"] else "user"
        messages.append({"role": r, "content": msg.get("content", "")})
        
    result_json = None
    
    if req.openaiKey:
        headers = {"Authorization": f"Bearer {req.openaiKey}", "Content-Type": "application/json"}
        data = {
            "model": req.modelSelection or "gpt-4o-mini",
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if res.ok:
            result_json = json.loads(res.json()["choices"][0]["message"]["content"].strip())
            
    if not result_json and req.groqKey:
        headers = {"Authorization": f"Bearer {req.groqKey}", "Content-Type": "application/json"}
        data = {
            "model": req.modelSelection or "llama3-70b-8192",
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        if res.ok:
            result_json = json.loads(res.json()["choices"][0]["message"]["content"].strip())
            
    if not result_json and os.getenv("GEMINI_API_KEY"):
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            # For Gemini we pass system prompt as first message or instructions
            from google.genai import types
            gemini_messages = []
            for msg in messages:
                gemini_messages.append(
                    types.Content(
                        role="user" if msg["role"] in ["system", "user"] else "model",
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=gemini_messages,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            result_json = json.loads(response.text.strip())
        except Exception as e:
            print("Gemini error:", e)

    if not result_json:
        result_json = {
            "state": "Speaking",
            "speech": "I processed this locally via Python fallback.",
            "action": "NONE",
            "targetDevice": "NONE",
            "logs": ["Local python backend processing.", f"Command: {command}"],
            "notifications": []
        }
        
    if result_json.get("action") == "MONITORING":
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        result_json["speech"] = f"Your CPU usage is at {cpu}%. You're using {mem.percent}% of your RAM."
        result_json["logs"] = [f"[SYSINFO] CPU: {cpu}%", f"[SYSINFO] RAM: {mem.percent}%"]

    if result_json.get("sysCommand") or result_json.get("action") != "NONE":
        append_audit_log(command, result_json.get("action", "NONE"), result_json.get("sysCommand", ""), result_json.get("requiresPrivilege", False))
        
    save_message('user', command)
    save_message('assistant', result_json.get("speech", ""))
    
    result_json["geminiActive"] = bool(os.getenv("GEMINI_API_KEY"))
    return result_json

class ExecuteRequest(BaseModel):
    sysCommand: str
    category: str = "RAW_COMMAND"

from backend.agents.git_agent import GitAgent

@app.post("/api/luna/execute")
async def luna_execute(req: ExecuteRequest):
    if req.category == "GIT_AUTOMATION":
        agent = GitAgent()
        result = await agent.execute("", git_cmd=req.sysCommand)
        return result

    result = await execute_system_command(req.sysCommand, req.category)
    return result

class TTSRequest(BaseModel):
    text: str
    provider: str = "edge"
    voiceId: str = ""
    elevenLabsApiKey: str = ""
    speed: float = 1.0
    pitch: float = 1.0

@app.post("/api/tts")
async def tts(req: TTSRequest):
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
            with open(tmp_file, "wb") as f:
                f.write(res.content)
        else:
            voice = req.voiceId or "en-US-AriaNeural"
            rate_str = f"+{int((req.speed - 1)*100)}%" if req.speed > 1 else f"{int((req.speed - 1)*100)}%" if req.speed != 1.0 else "+0%"
            pitch_str = f"+{int((req.pitch - 1)*50)}Hz" if req.pitch > 1 else f"{int((req.pitch - 1)*50)}Hz" if req.pitch != 1.0 else "+0Hz"
            
            communicate = edge_tts.Communicate(req.text, voice, rate=rate_str, pitch=pitch_str)
            await communicate.save(tmp_file)
            
        with open(tmp_file, "rb") as f:
            audio_data = f.read()
        return Response(content=audio_data, media_type="audio/mpeg")
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

@app.post("/api/stt")
async def stt(audio: UploadFile = File(...)):
    # Save uploaded file
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
            text = recognizer.recognize_google(audio_data)
            
        return {"transcript": text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(tmp_in): os.remove(tmp_in)
        if os.path.exists(tmp_out): os.remove(tmp_out)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=True)
