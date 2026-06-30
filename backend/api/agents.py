import os
import glob
import subprocess
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
import psutil

router = APIRouter(prefix="/agents")

# --- Browser Agent ---
class BrowserRequest(BaseModel):
    action: str
    url: str = ""

@router.post("/browser")
async def browser_agent(req: BrowserRequest):
    # E.g. xdg-open for URL opening, or beautifulsoup for scraping
    if req.action == "open":
        subprocess.Popen(["xdg-open", req.url])
        return {"status": "success", "result": f"Opened {req.url}"}
    return {"status": "success", "agent": "BrowserAgent", "result": "Action processed"}

# --- File Agent ---
class FileRequest(BaseModel):
    action: str
    path: str = ""
    content: str = ""

@router.post("/file")
async def file_agent(req: FileRequest):
    try:
        if req.action == "read":
            with open(req.path, "r") as f:
                return {"status": "success", "result": f.read()}
        elif req.action == "write":
            with open(req.path, "w") as f:
                f.write(req.content)
            return {"status": "success", "result": f"File {req.path} written."}
        elif req.action == "search":
            results = glob.glob(req.path, recursive=True)
            return {"status": "success", "result": results}
    except Exception as e:
        return {"status": "error", "result": str(e)}

# --- Terminal Agent ---
class TerminalRequest(BaseModel):
    command: str

@router.post("/terminal")
async def terminal_agent(req: TerminalRequest):
    try:
        proc = await asyncio.create_subprocess_shell(
            req.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return {
            "status": "success",
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
            "exit_code": proc.returncode
        }
    except Exception as e:
         return {"status": "error", "result": str(e)}

# --- GitHub Agent ---
class GithubRequest(BaseModel):
    action: str
    repo: str = ""
    
@router.post("/github")
async def github_agent(req: GithubRequest):
    if req.action == "status":
        proc = subprocess.run(["git", "-C", req.repo, "status"], capture_output=True, text=True)
        return {"status": "success", "result": proc.stdout}
    return {"status": "success", "result": "Git action simulated."}

# --- Media Agent ---
class MediaRequest(BaseModel):
    action: str

@router.post("/media")
async def media_agent(req: MediaRequest):
    # Using playerctl as a linux media controller
    if req.action in ["play-pause", "next", "previous", "stop"]:
        subprocess.Popen(["playerctl", req.action])
        return {"status": "success", "result": f"Executed media {req.action}"}
    return {"status": "error", "result": "Invalid media action"}

# --- Device & System Agent ---
@router.get("/device/telemetry")
async def device_telemetry():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "cpu": cpu,
        "ram": ram.percent,
        "disk": disk.percent,
        "battery": 100 # Mock unless python-upower is used
    }
