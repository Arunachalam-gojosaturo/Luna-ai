import os
import glob
import subprocess
import asyncio
import mimetypes
from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
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
    from backend.utils.sys_control import system_controller
    if req.action in ["play", "pause", "play-pause", "next", "previous", "stop"]:
        success = system_controller.control_media(req.action)
        return {"status": "success" if success else "error", "result": f"Executed media {req.action}"}
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

# --- ADB Agent ---
class ADBConnectRequest(BaseModel):
    target: str

class ADBControlRequest(BaseModel):
    action: str
    target: str = ""
    text: str = ""
    x: int = 0
    y: int = 0

class ADBLaunchAppRequest(BaseModel):
    app: str
    target: str = ""

class ADBTcpIpRequest(BaseModel):
    serial: str
    port: str = "5555"

class ADBDisconnectRequest(BaseModel):
    target: str

@router.get("/adb/devices")
async def adb_devices():
    try:
        from backend.utils.adb_manager import adb_manager
        devices = await adb_manager.scan_and_auto_connect()
        return {"status": "success", "devices": devices}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/adb/connect")
async def adb_connect(req: ADBConnectRequest):
    try:
        proc = await asyncio.create_subprocess_exec(
            "adb", "connect", req.target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode().strip()
        err = stderr.decode().strip()
        success = "connected" in out.lower()
        return {"status": "success" if success else "error", "stdout": out, "stderr": err}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/adb/tcpip")
async def adb_tcpip(req: ADBTcpIpRequest):
    try:
        proc = await asyncio.create_subprocess_exec(
            "adb", "-s", req.serial, "tcpip", req.port,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode().strip()
        err = stderr.decode().strip()
        success = proc.returncode == 0 or "restarting" in out.lower()
        return {"status": "success" if success else "error", "stdout": out, "stderr": err}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/adb/disconnect")
async def adb_disconnect(req: ADBDisconnectRequest):
    try:
        proc = await asyncio.create_subprocess_exec(
            "adb", "disconnect", req.target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode().strip()
        err = stderr.decode().strip()
        return {"status": "success", "stdout": out, "stderr": err}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/adb/scrcpy")
async def adb_scrcpy(req: ADBConnectRequest):
    try:
        cmd = ["scrcpy"]
        if req.target:
            cmd.extend(["-s", req.target])
        subprocess.Popen(cmd)
        return {"status": "success", "result": "Launched scrcpy in background"}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/adb/control")
async def adb_control(req: ADBControlRequest):
    try:
        from backend.utils.adb_manager import adb_manager
        res = await adb_manager.control_input(req.action, req.text, req.x, req.y, req.target)
        return res
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/adb/launch_app")
async def adb_launch_app(req: ADBLaunchAppRequest):
    try:
        from backend.utils.adb_manager import adb_manager
        res = await adb_manager.launch_app(req.app, req.target)
        return res
    except Exception as e:
        return {"status": "error", "result": str(e)}


# --- WhatsApp Agent ---
from backend.agents.whatsapp_agent import whatsapp_manager

@router.post("/whatsapp/start")
async def start_whatsapp():
    return whatsapp_manager.start()

@router.post("/whatsapp/stop")
async def stop_whatsapp():
    return whatsapp_manager.stop()

@router.get("/whatsapp/status")
async def status_whatsapp():
    return whatsapp_manager.get_status()

# --- GitHub Agent ---
from backend.agents.github_agent import github_agent

@router.get("/github/repos")
async def get_github_repos(token: str):
    if not token:
        return {"status": "error", "message": "Missing token"}
    try:
        repos = await github_agent.get_user_repos(token)
        return {"status": "success", "repos": repos}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/github/repo_details")
async def get_github_repo_details(token: str, owner: str, repo: str):
    if not token or not owner or not repo:
        return {"status": "error", "message": "Missing required parameters"}
    try:
        details = await github_agent.get_repo_details(token, owner, repo)
        return {"status": "success", "details": details}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/github/profile")
async def get_github_profile(token: str):
    if not token:
        return {"status": "error", "message": "Missing token"}
    try:
        profile = await github_agent.get_user_profile(token)
        return {"status": "success", "profile": profile}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/github/repo_extended")
async def get_github_repo_extended(token: str, owner: str, repo: str):
    if not token or not owner or not repo:
        return {"status": "error", "message": "Missing required parameters"}
    try:
        extended = await github_agent.get_repo_extended_details(token, owner, repo)
        return {"status": "success", "extended": extended}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/files/list")
async def list_files(path: str):
    if not path:
        return {"status": "error", "message": "Path is required"}
    try:
        expanded_path = os.path.expanduser(path)
        if not os.path.exists(expanded_path):
            return {"status": "error", "message": "Path does not exist"}
        if not os.path.isdir(expanded_path):
            return {"status": "error", "message": "Path is not a directory"}
        
        items = []
        for entry in os.scandir(expanded_path):
            if entry.name in [".git", "node_modules", "__pycache__", ".venv", "venv"]:
                continue
            is_dir = entry.is_dir()
            try:
                size = entry.stat().st_size if not is_dir else 0
            except Exception:
                size = 0
            items.append({
                "name": entry.name,
                "isDir": is_dir,
                "size": size,
                "path": entry.path.replace('\\', '/')
            })
        items.sort(key=lambda x: (not x["isDir"], x["name"].lower()))
        return {
            "status": "success",
            "files": items,
            "parent": os.path.dirname(expanded_path).replace('\\', '/')
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/files/content")
async def get_file_content(path: str):
    if not path:
        return Response(content="Path is required", status_code=400)
    try:
        expanded_path = os.path.expanduser(path)
        if not os.path.exists(expanded_path):
            return Response(content="File not found", status_code=404)
        if os.path.isdir(expanded_path):
            return Response(content="Cannot view a directory", status_code=400)
        
        mime_type, _ = mimetypes.guess_type(expanded_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        return FileResponse(expanded_path, media_type=mime_type)
    except Exception as e:
        return Response(content=str(e), status_code=500)



