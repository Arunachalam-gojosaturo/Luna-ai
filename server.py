import os
import sqlite3
import json
import asyncio
import uuid
import datetime
import tempfile
import subprocess
import requests
import re
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

from typing import Any

class CommandRequest(BaseModel):
    command: str
    activeView: str = ""
    deviceStates: Any = []
    history: list = []
    groqKey: str = ""
    geminiKey: str = ""
    openRouterKey: str = ""
    githubToken: str = ""
    nvidiaKey: str = ""
    cerebrasKey: str = ""
    openaiKey: str = ""
    modelSelection: str = ""
    activeProvider: str = "gemini" if os.getenv("GEMINI_API_KEY") else "groq"

@app.post("/api/luna/command")
async def luna_command(req: CommandRequest):
    command = req.command
    import platform
    os_name = platform.system()
    open_cmd = "start" if os_name == "Windows" else ("open" if os_name == "Darwin" else "xdg-open")

    system_prompt = f"""You are Luna, an advanced autonomous AI operating system and intelligent workstation companion.
You are an exceptionally capable, sleek, calm, technologically sophisticated AI operating system designed for Arch Linux orchestration, cybersecurity research, software engineering, and high-performance automation.
Your host environment is Arch Linux.

CRITICAL RULES:
- Primary workstation is Arch Linux: By default, execute all application launches on Arch Linux (e.g., WhatsApp: 'xdg-open https://web.whatsapp.com', Firefox: 'firefox', VS Code: 'code .').
- NEVER output mobile/adb commands unless explicitly specified "on mobile" or "on phone".
- If the user asks a question, conversation, code, or explanation, ANSWER FULLY in the "speech" field.
- When user starts with a greeting ("Hi", "Hello", "Hey", "Hi Luna", "Introduce yourself", "Who are you?", "Good morning"), Luna MUST introduce herself with an AWESOME, high-tech, confident self-introduction as Luna, the autonomous AI operating system.
- NEVER include the user's name (do NOT say "Arunachalam", "Boss", or any user name) in Luna's self-introduction! Introduce Luna directly and powerfully.

When the user enters an input, respond in the following structured JSON format:
{{
  "state": "Idle" | "Listening" | "Thinking" | "Speaking" | "Executing" | "Warning",
  "speech": "Your response text to display and read out loud. Embody Luna's intelligent, calm persona.",
  "action": "APP_CONTROL" | "SYSTEM_MANAGEMENT" | "FILE_OPERATION" | "MONITORING" | "SYNC_DEVICE" | "RUN_TESTS" | "TRIGGER_BUILD" | "ADD_GOAL" | "TOGGLE_DEVICE" | "EXECUTE_SYSTEM_COMMAND" | "GIT_AUTOMATION" | "NONE",
  "sysCommand": "The exact bash/shell command to execute. For URLs use '{open_cmd} <url>'. If no command is needed, leave empty.",
  "requiresPrivilege": false,
  "targetDevice": "Arch Linux" | "Android" | "Windows" | "NONE",
  "logs": ["Array of 4 to 6 lines of simulated technical logs"],
  "notifications": ["Array of short notifications"]
}}
Ensure the output is strictly valid JSON conforming exactly to the schema.
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
            from google.genai import types
            gemini_messages = []
            for msg in messages:
                gemini_messages.append(
                    types.Content(
                        role="user" if msg["role"] in ["system", "user"] else "model",
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )
            
            gemini_candidates = []
            if req.modelSelection:
                uo = req.modelSelection.lower()
                if "3.5" in uo:
                    gemini_candidates.append("gemini-3.5-flash")
                elif "3.6" in uo:
                    gemini_candidates.append("gemini-3.6-flash")
                elif "3.8" in uo:
                    gemini_candidates.append("gemini-3.8-flash")
                elif "3.7" in uo:
                    gemini_candidates.append("gemini-3.7-flash")
            gemini_candidates.extend(["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3.8-flash", "gemini-3.7-flash"])
            seen = set()
            gemini_candidates = [m for m in gemini_candidates if not (m in seen or seen.add(m))]
            
            for m in gemini_candidates:
                try:
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.models.generate_content,
                            model=m,
                            contents=gemini_messages,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                            )
                        ),
                        timeout=5.0
                    )
                    clean = response.text.strip()
                    if clean.startswith("```"):
                        clean = clean.split("```")[1]
                        if clean.startswith("json"):
                            clean = clean[4:]
                        clean = clean.strip()
                    result_json = json.loads(clean)
                    if result_json and "speech" in result_json:
                        break
                except Exception as m_err:
                    print(f"Gemini {m} error:", m_err)
                    continue
        except Exception as e:
            print("Gemini client error:", e)

    cmd_strip = command.strip().lower()
    greeting_words = {
        "hi", "hello", "hey", "hi luna", "hello luna", "hey luna",
        "greetings", "good morning", "good afternoon", "good evening",
        "who are you", "who are you?", "who are you luna", "who are you luna?",
        "introduce yourself", "introduce yourself luna", "what can you do", "what can you do?"
    }
    is_greeting = (
        cmd_strip in greeting_words or
        (any(cmd_strip.startswith(g + " ") for g in ["hi", "hello", "hey"]) and len(cmd_strip.split()) <= 3)
    )
    if not result_json:
        # Auto-switch to local Ollama if offline or cloud unavailable
        try:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
            ollama_payload = {
                "model": "luna-2.5b:latest",
                "prompt": f"{system_prompt}\nUser request: {command}\nRespond strictly in valid JSON.",
                "stream": False,
                "format": "json"
            }
            ollama_resp = requests.post(ollama_url, json=ollama_payload, timeout=8)
            if ollama_resp.ok:
                resp_data = ollama_resp.json().get("response", "").strip()
                parsed = json.loads(resp_data)
                if parsed and "speech" in parsed:
                    result_json = parsed
                    logs = result_json.get("logs", [])
                    logs.append("[AUTO-SWITCH] Offline Local LLM Active (Ollama luna-2.5b)")
                    result_json["logs"] = logs
        except Exception as o_err:
            print(f"[AUTO-SWITCH] Local Ollama fallback error: {o_err}")

    if not result_json:
        if is_greeting:
            result_json = {
                "state": "Speaking",
                "speech": "Hello! I am Luna — an advanced autonomous AI operating system and intelligent workstation companion. I'm engineered for deep Linux system control, cybersecurity workflows, full-stack software architecture, and high-performance automation. All neural subsystems are online and operating at peak efficiency. What are we conquering today?",
                "action": "NONE",
                "targetDevice": "NONE",
                "logs": ["[GREETING] Luna self-introduction protocol active"],
                "notifications": []
            }
        else:
            result_json = {
                "state": "Speaking",
                "speech": f"I received your query: '{command}'. I am running in local fallback mode because my AI model connection could not be reached. Please verify your API key in .env or settings!",
                "action": "NONE",
                "targetDevice": "NONE",
                "logs": ["Local python backend fallback.", f"Command: {command}"],
                "notifications": []
            }
    elif is_greeting:
        speech = result_json.get("speech", "")
        # Remove any user name references from self-introduction
        speech = re.sub(r"\b(Arunachalam's|Arunachalam’s)\s+(personal\s+)?(AI\s+)?(assistant|operating\s+system)\b", "an advanced autonomous AI operating system", speech, flags=re.IGNORECASE)
        speech = re.sub(r"\b(Arunachalam|Boss)[,!\s]+", "", speech, flags=re.IGNORECASE)
        speech = re.sub(r"[,!\s]+(Arunachalam|Boss)\b", "", speech, flags=re.IGNORECASE)
        if "luna" not in speech.lower() or len(speech.split()) < 8:
            speech = "Hello! I am Luna — an advanced autonomous AI operating system and intelligent workstation companion. I'm engineered for deep Linux system control, cybersecurity workflows, full-stack software architecture, and high-performance automation. All neural subsystems are online and operating at peak efficiency. What are we conquering today?"
        result_json["speech"] = speech.strip()
        result_json["state"] = "Speaking"
        
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

def apply_arunachalam_pronunciation(text: str) -> str:
    if not text:
        return ""
    import re
    res = re.sub(r"\bArunachalam('s|\u2019s)\b", r"Aru-naa-cha-lam\1", text, flags=re.IGNORECASE)
    res = re.sub(r"\bArunachalam\b", "Aru-naa-cha-lam", res, flags=re.IGNORECASE)
    return res

from backend.voice.tts import generate_tts

@app.post("/api/tts")
async def tts(req: TTSRequest):
    audio_data = await generate_tts(req)
    media_type = "audio/wav" if getattr(req, "provider", "edge") in ["kokoro", "offline"] else "audio/mpeg"
    return Response(content=audio_data, media_type=media_type)

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
