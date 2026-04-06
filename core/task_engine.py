"""
Luna Task Engine v6 — RUNS BEFORE AI EVERY TIME.
Returns TaskResult → AI skipped.
Returns None       → AI runs.
"""
import os, re, subprocess, sys
from pathlib import Path
from core.env_helper   import env
from core.system_ctrl  import BrightnessCtrl, VolumeCtrl
from core.youtube_ctrl import YouTubeController


class TaskResult:
    def __init__(self, ok: bool, msg: str, out: str = "", output: str = ""):
        self.success = ok
        self.message = msg
        self.output  = output if output else out


class TaskEngine:
    def __init__(self, mem):
        self.mem=mem; self._br=BrightnessCtrl()
        self._vol=VolumeCtrl(); self._yt=YouTubeController()

    @property
    def workspace(self) -> Path:
        d = Path(self.mem.get("workspace_dir", str(Path.home()/"LunaWorkspace")))
        d.mkdir(parents=True,exist_ok=True); return d

    @property
    def music_dir(self) -> Path:
        d = Path(self.mem.get("download_dir", str(Path.home()/"Music")))
        d.mkdir(parents=True,exist_ok=True); return d

    def handle(self, raw: str):
        t=raw.strip(); tl=t.lower()
        for ww in ("luna, ","luna ","hey luna, ","hey luna "):
            if tl.startswith(ww): tl=tl[len(ww):].strip(); t=t[len(ww):].strip(); break

        # BRIGHTNESS
        bc = self._parse_bright(tl)
        if bc: return self._do_bright(bc)

        # VOLUME
        vc = self._parse_vol(tl)
        if vc: return self._do_vol(vc)

        # YOUTUBE controls
        if re.search(r"\b(pause|resume)\b",tl) and re.search(r"\b(video|youtube|song|music)\b",tl):
            self._yt.pause_resume(); return TaskResult(True,"YouTube paused/resumed.")
        if re.search(r"\bmute\b",tl) and re.search(r"\b(video|youtube)\b",tl):
            self._yt.mute_video(); return TaskResult(True,"YouTube muted.")

        # PLAY → YouTube
        m = re.search(r"^(?:play|put on|start|open|watch|search|find)\s+(?:the\s+)?(?:song|video|music|track|audio\s+)?(.+?)(?:\s+on\s+(?:youtube|yt|firefox))?\s*$",t,re.IGNORECASE)
        if m:
            q=m.group(1).strip()
            if not re.match(r"^(volume|brightness|bright|screen|mute|unmute)\b",q.lower()):
                ok,msg=self._yt.search_and_play(q); return TaskResult(ok,msg,output="YouTube: "+q)

        # DOWNLOAD mp3
        m = re.search(r"^download\s+(?:song|music|audio|track\s+)?(.+)$",t,re.IGNORECASE)
        if m: return self._dl_mp3(m.group(1).strip())

        # SHELL
        m = re.search(r"^(?:run|execute|shell|cmd|bash|sudo)\s+(.+)$",t,re.IGNORECASE)
        if m: return self._shell(m.group(1))

        # INSTALL
        m = re.search(r"^install\s+(?:package\s+)?(\S+)",tl)
        if m: return self._install(m.group(1))

        # CREATE DIR
        m = re.search(r"create\s+(?:a\s+)?(?:dir(?:ectory)?|folder)\s+(?:called?|named?)?\s*['\"]?(\S+)['\"]?",tl)
        if m: return self._mkdir(m.group(1))

        # CREATE FILE
        m = re.search(r"create\s+(?:a\s+)?file\s+(?:called?|named?)?\s*['\"]?([\w.\-]+)['\"]?",tl)
        if m: return self._touch(m.group(1))

        # LIST
        if re.search(r"^(?:list|ls|show)\s+(?:files?|workspace)",tl): return self._ls()

        # STATUS
        if re.search(r"(?:brightness|volume|sound)\s+(?:status|level|current|percent)",tl):
            b=self._br.get(); v=self._vol.get()
            parts=[]
            if b>=0: parts.append("Brightness: "+str(b)+"%")
            if v>=0: parts.append("Volume: "+str(v)+"%")
            return TaskResult(True," | ".join(parts) or "Could not read levels.")

        return None  # → AI handles

    # ── Brightness ────────────────────────────────────────────────────────
    def _parse_bright(self, tl):
        if not re.search(r"\b(bright(?:ness)?|screen|display|backlight|dim|monitor)\b",tl): return None
        if re.search(r"\b(max(?:imum)?|full|100)\b",tl):         return {"a":"max"}
        if re.search(r"\b(min(?:imum)?|lowest|very\s*low|dark)\b",tl): return {"a":"min"}
        if re.search(r"\b(up|increase|brighter|higher|raise|more|boost)\b",tl):
            m=re.search(r"(\d+)",tl); return {"a":"up","s":min(int(m.group(1)),100) if m else 10}
        if re.search(r"\b(down|decrease|dim(?:mer)?|lower|reduce|less|darker)\b",tl):
            m=re.search(r"(\d+)",tl); return {"a":"down","s":min(int(m.group(1)),100) if m else 10}
        m=re.search(r"(\d{1,3})\s*%?",tl)
        if m: return {"a":"set","v":min(int(m.group(1)),100)}
        return None

    def _do_bright(self, c) -> TaskResult:
        if not self._br.available():
            return TaskResult(False,"brightnessctl not found.\nFix: sudo pacman -S brightnessctl && sudo usermod -aG video $USER")
        a=c["a"]
        if   a=="max":  ok,msg=self._br.max_b()
        elif a=="min":  ok,msg=self._br.min_b()
        elif a=="up":   ok,msg=self._br.up(c.get("s",10))
        elif a=="down": ok,msg=self._br.down(c.get("s",10))
        elif a=="set":  ok,msg=self._br.set_pct(c.get("v",50))
        else: return TaskResult(False,"Unknown brightness command.")
        return TaskResult(ok,msg)

    # ── Volume ────────────────────────────────────────────────────────────
    def _parse_vol(self, tl):
        if re.search(r"\b(mic|microphone)\b",tl):
            if "unmute" in tl: return {"a":"mic_unmute"}
            if "mute"   in tl: return {"a":"mic_mute"}
        if re.search(r"\bunmute\b",tl): return {"a":"unmute"}
        if re.search(r"\bmute\b",tl) and not re.search(r"\b(youtube|video)\b",tl): return {"a":"mute"}
        if re.search(r"\b(vol(?:ume)?|sound|audio)\b",tl):
            if re.search(r"\b(max(?:imum)?|full|100|loudest)\b",tl):    return {"a":"set","v":100}
            if re.search(r"\b(min(?:imum)?|zero|silent|quietest|0)\b",tl): return {"a":"set","v":0}
        if re.search(r"\b(vol(?:ume)?\s*up|louder|increase\s*(?:the\s*)?vol|raise\s*(?:the\s*)?vol|turn\s*(?:it\s*|the\s*vol\s*)?up|sound\s*up|audio\s*up)\b",tl):
            m=re.search(r"(\d+)",tl); return {"a":"up","s":min(int(m.group(1)),100) if m and int(m.group(1))<=100 else 10}
        if re.search(r"\b(vol(?:ume)?\s*down|quieter|decrease\s*(?:the\s*)?vol|lower\s*(?:the\s*)?vol|turn\s*(?:it\s*|the\s*vol\s*)?down|sound\s*down|audio\s*down)\b",tl):
            m=re.search(r"(\d+)",tl); return {"a":"down","s":min(int(m.group(1)),100) if m and int(m.group(1))<=100 else 10}
        m=re.search(r"(?:set\s+)?(?:vol(?:ume)?|sound|audio)\s+(?:to\s+|at\s+)?(\d{1,3})\s*%?",tl)
        if m: return {"a":"set","v":min(int(m.group(1)),150)}
        return None

    def _do_vol(self, c) -> TaskResult:
        if not self._vol.available():
            return TaskResult(False,"wpctl/pactl not found.\nFix: sudo pacman -S pipewire pipewire-pulse wireplumber")
        a=c["a"]
        if   a=="mute":       ok,msg=self._vol.mute()
        elif a=="unmute":     ok,msg=self._vol.unmute()
        elif a=="up":         ok,msg=self._vol.up(c.get("s",10))
        elif a=="down":       ok,msg=self._vol.down(c.get("s",10))
        elif a=="set":        ok,msg=self._vol.set_pct(c.get("v",50))
        elif a=="mic_mute":   ok,msg=self._vol.mic_mute()
        elif a=="mic_unmute": ok,msg=self._vol.mic_unmute()
        else: return TaskResult(False,"Unknown volume command.")
        return TaskResult(ok,msg)

    # ── Download MP3 ──────────────────────────────────────────────────────
    def _dl_mp3(self, query) -> TaskResult:
        out = str(self.music_dir/"%(title)s.%(ext)s")
        try:
            r = subprocess.run([sys.executable,"-m","yt_dlp",f"ytsearch1:{query}",
                                "--extract-audio","--audio-format","mp3","--audio-quality","0",
                                "-o",out,"--no-playlist","--print","after_move:filepath","--no-warnings"],
                               capture_output=True,text=True,timeout=120,env={**env(),"TMPDIR":"/tmp"})
            path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
            if not path or not Path(path).exists():
                files = sorted(self.music_dir.glob("*.mp3"),key=os.path.getmtime,reverse=True)
                path = str(files[0]) if files else ""
            if not path: return TaskResult(False,"Download failed: "+(r.stderr or r.stdout)[:200])
            return TaskResult(True,"Downloaded: "+Path(path).name,output="Saved: "+path)
        except subprocess.TimeoutExpired: return TaskResult(False,"Download timed out.")
        except Exception as e: return TaskResult(False,"Error: "+str(e))

    def _mkdir(self, name):
        try: t=self.workspace/name; t.mkdir(parents=True,exist_ok=True); return TaskResult(True,"Created: "+str(t))
        except Exception as e: return TaskResult(False,str(e))

    def _touch(self, name, content=""):
        try:
            t=self.workspace/name; t.parent.mkdir(parents=True,exist_ok=True); t.write_text(content)
            return TaskResult(True,"Created: "+str(t),out=str(t))
        except Exception as e: return TaskResult(False,str(e))

    def write_code(self, filename, code, lang=""):
        ext={"python":"py","py":"py","javascript":"js","js":"js","bash":"sh","sh":"sh","html":"html","css":"css","rust":"rs"}
        if "." not in filename: filename+="."+ext.get(lang.lower(),"txt")
        try:
            t=self.workspace/filename; t.parent.mkdir(parents=True,exist_ok=True); t.write_text(code)
            if filename.endswith(".sh"): os.chmod(t,0o755)
            return TaskResult(True,"Saved: "+str(t),out=str(t))
        except Exception as e: return TaskResult(False,str(e))

    def _shell(self, cmd):
        try:
            r=subprocess.run(cmd,shell=True,capture_output=True,text=True,
                             timeout=60,cwd=str(self.workspace),env=env())
            out=(r.stdout+r.stderr).strip(); ok=r.returncode==0
            return TaskResult(ok,"Done (exit "+str(r.returncode)+").",out=out or "(no output)")
        except subprocess.TimeoutExpired: return TaskResult(False,"Timed out.")
        except Exception as e: return TaskResult(False,str(e))

    def _install(self, pkg):
        for cmd in [[sys.executable,"-m","pip","install",pkg,"-q"],
                    ["sudo","pacman","-S",pkg,"--noconfirm"],["yay","-S",pkg,"--noconfirm"]]:
            try:
                r=subprocess.run(cmd,capture_output=True,text=True,timeout=120,env={**env(),"TMPDIR":"/tmp"})
                if r.returncode==0: return TaskResult(True,"Installed "+pkg+".")
            except (FileNotFoundError,subprocess.TimeoutExpired): continue
        return TaskResult(False,"Could not install "+pkg+".")

    def _ls(self):
        files=list(self.workspace.rglob("*"))
        if not files: return TaskResult(True,"Workspace is empty.")
        lines=["📁 "+str(f.relative_to(self.workspace)) if f.is_dir() else "📄 "+str(f.relative_to(self.workspace)) for f in sorted(files)[:50]]
        return TaskResult(True,str(len(files))+" items:",out="\n".join(lines))
