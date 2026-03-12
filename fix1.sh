#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#  LUNA AI — NUKE FIX
#  THE REAL PROBLEM: AI was running BEFORE task engine
#  This script fixes the execution order permanently
#  cd ~/Music/Luna-AI-v5 && chmod +x luna_nuke_fix.sh && ./luna_nuke_fix.sh
# ═══════════════════════════════════════════════════════
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

GRN='\033[0;32m'; YLW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()  { echo -e "  ${GRN}[✓]${NC} $1"; }
inf() { echo -e "  ${YLW}[→]${NC} $1"; }
err() { echo -e "  ${RED}[!]${NC} $1"; }

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   LUNA AI — NUKE FIX                       ║"
echo "  ║   Fixes: AI fake responses, YouTube,        ║"
echo "  ║   Volume, Brightness                        ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""

[ -f "$DIR/.venv/bin/activate" ] && source "$DIR/.venv/bin/activate"
PYTHON="${PYTHON:-python3}"

# ───────────────────────────────────────────────────────
# STEP 1: System tools
# ───────────────────────────────────────────────────────
inf "Checking system tools..."

command -v brightnessctl &>/dev/null || sudo pacman -S --noconfirm brightnessctl
ok "brightnessctl: $(brightnessctl | grep -oP '\d+(?=%)'| head -1)%"

groups "$USER" | grep -qw video || { sudo usermod -aG video "$USER"; err "Added to video group — re-login or run: newgrp video"; }
ok "video group: ok"

command -v wpctl &>/dev/null || sudo pacman -S --noconfirm pipewire pipewire-pulse wireplumber
ok "wpctl: $(wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null | tr -d '\n')"

command -v firefox &>/dev/null && ok "firefox: found" || err "Install: sudo pacman -S firefox"
command -v xdotool &>/dev/null || sudo pacman -S --noconfirm xdotool 2>/dev/null || true
command -v xdotool &>/dev/null && ok "xdotool: found" || inf "xdotool optional (browser keys)"

$PYTHON -m pip install -q --upgrade yt-dlp
ok "yt-dlp: $($PYTHON -m yt_dlp --version 2>/dev/null)"

echo ""
inf "Writing all Python files..."

# ───────────────────────────────────────────────────────
# core/system_ctrl.py
# ───────────────────────────────────────────────────────
cat > "$DIR/core/system_ctrl.py" << 'PY'
import re, subprocess, shutil, glob


def _r(*cmd):
    return subprocess.run(list(cmd), capture_output=True, text=True)


class BrightnessCtrl:
    @staticmethod
    def available():
        return bool(shutil.which("brightnessctl"))

    def get(self) -> int:
        # Try brightnessctl
        try:
            cur = int(_r("brightnessctl","get").stdout.strip())
            mx  = int(_r("brightnessctl","max").stdout.strip())
            return round(cur/mx*100) if mx else 0
        except Exception:
            pass
        # Fallback: sysfs
        for d in glob.glob("/sys/class/backlight/*/"):
            try:
                cur = int(open(d+"brightness").read())
                mx  = int(open(d+"max_brightness").read())
                return round(cur/mx*100)
            except Exception:
                pass
        return -1

    def _bcset(self, *args) -> bool:
        for prefix in [["brightnessctl"], ["sudo","-n","brightnessctl"]]:
            r = subprocess.run(prefix+list(args), capture_output=True, text=True)
            if r.returncode == 0:
                return True
        # Last resort: write directly to sysfs
        for d in glob.glob("/sys/class/backlight/*/"):
            try:
                mx = int(open(d+"max_brightness").read())
                # Parse the arg to get value
                arg = args[-1] if args else "50%"
                pct = int(arg.replace("%","").replace("+","").replace("-",""))
                newval = int(mx * pct / 100)
                with open(d+"brightness","w") as f:
                    f.write(str(newval))
                return True
            except Exception:
                pass
        return False

    def set_pct(self, pct:int):
        pct = max(1,min(100,pct))
        ok = self._bcset("set",f"{pct}%")
        cur = self.get()
        return ok, f"Brightness {'set to '+str(pct)+'%' if ok else 'failed. Run: sudo usermod -aG video $USER then re-login'}." + (f" Current: {cur}%" if ok else "")

    def up(self, step=10):
        ok = self._bcset("set",f"+{step}%")
        cur = self.get()
        return ok, f"Brightness up to {cur}%."

    def down(self, step=10):
        ok = self._bcset("set",f"{step}%-")
        cur = self.get()
        return ok, f"Brightness down to {cur}%."

    def max_b(self):
        ok = self._bcset("set","100%")
        return ok, "Brightness at max."

    def min_b(self):
        ok = self._bcset("set","5%")
        return ok, "Brightness at minimum."


class VolumeCtrl:
    SINK = "@DEFAULT_AUDIO_SINK@"
    SRC  = "@DEFAULT_AUDIO_SOURCE@"

    @staticmethod
    def available():
        return any(shutil.which(t) for t in ["wpctl","pactl","amixer"])

    def get(self) -> int:
        try:
            r = _r("wpctl","get-volume","@DEFAULT_AUDIO_SINK@")
            m = re.search(r"Volume:\s*([\d.]+)", r.stdout)
            if m: return int(float(m.group(1))*100)
        except Exception: pass
        try:
            r = _r("pactl","get-sink-volume","@DEFAULT_SINK@")
            m = re.search(r"(\d+)%", r.stdout)
            if m: return int(m.group(1))
        except Exception: pass
        return -1

    def is_muted(self):
        try: return "MUTED" in _r("wpctl","get-volume","@DEFAULT_AUDIO_SINK@").stdout
        except Exception: return False

    def _do(self, *wp_args):
        r = _r("wpctl", *wp_args)
        if r.returncode == 0: return True
        # pactl fallback mapping
        mapping = {
            ("set-volume", self.SINK): lambda v: _r("pactl","set-sink-volume","@DEFAULT_SINK@",v),
            ("set-mute",   self.SINK): lambda v: _r("pactl","set-sink-mute","@DEFAULT_SINK@",v),
        }
        return r.returncode == 0

    def set_pct(self, pct:int):
        pct = max(0,min(150,pct))
        fval = f"{pct/100:.2f}"
        r = _r("wpctl","set-volume",self.SINK,fval)
        if r.returncode != 0:
            _r("pactl","set-sink-volume","@DEFAULT_SINK@",f"{pct}%")
        cur = self.get()
        return True, f"Volume set to {pct}%. Current: {cur}%."

    def up(self, step=10):
        r = _r("wpctl","set-volume","-l","1.5",self.SINK,f"{step}%+")
        if r.returncode != 0:
            _r("pactl","set-sink-volume","@DEFAULT_SINK@",f"+{step}%")
        cur = self.get()
        return True, f"Volume up to {cur}%."

    def down(self, step=10):
        r = _r("wpctl","set-volume",self.SINK,f"{step}%-")
        if r.returncode != 0:
            _r("pactl","set-sink-volume","@DEFAULT_SINK@",f"-{step}%")
        cur = self.get()
        return True, f"Volume down to {cur}%."

    def mute(self):
        r = _r("wpctl","set-mute",self.SINK,"1")
        if r.returncode != 0: _r("pactl","set-sink-mute","@DEFAULT_SINK@","1")
        return True, "Muted."

    def unmute(self):
        r = _r("wpctl","set-mute",self.SINK,"0")
        if r.returncode != 0: _r("pactl","set-sink-mute","@DEFAULT_SINK@","0")
        return True, "Unmuted."

    def mic_mute(self):
        r = _r("wpctl","set-mute",self.SRC,"1")
        return (True,"Mic muted.") if r.returncode==0 else (False,"Mic mute failed.")

    def mic_unmute(self):
        r = _r("wpctl","set-mute",self.SRC,"0")
        return (True,"Mic unmuted.") if r.returncode==0 else (False,"Mic unmute failed.")
PY
ok "core/system_ctrl.py"

# ───────────────────────────────────────────────────────
# core/youtube_ctrl.py
# ───────────────────────────────────────────────────────
cat > "$DIR/core/youtube_ctrl.py" << 'PY'
"""Open YouTube video in Firefox by searching via yt-dlp (no download)."""
import subprocess, shutil, sys, time, urllib.parse


class YouTubeController:

    def search_and_play(self, query:str) -> tuple[bool,str]:
        vid, title = self._get_id(query)
        if vid:
            url  = f"https://www.youtube.com/watch?v={vid}"
            name = title or query
        else:
            url  = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
            name = query
        ok = self._open(url)
        if not ok:
            return False, "Firefox not found. Install: sudo pacman -S firefox"
        return True, f'Opened "{name}" on YouTube in Firefox.'

    def _get_id(self, query:str) -> tuple[str,str]:
        """yt-dlp metadata only — no audio/video download at all."""
        try:
            r = subprocess.run(
                [sys.executable,"-m","yt_dlp",
                 "--no-playlist","--quiet","--no-warnings",
                 "--print","%(id)s\t%(title)s",
                 f"ytsearch1:{query}"],
                capture_output=True, text=True, timeout=20)
            line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
            if "\t" in line:
                vid, title = line.split("\t", 1)
                return vid.strip(), title.strip()
            # fallback: old --get-id style
            r2 = subprocess.run(
                [sys.executable,"-m","yt_dlp",
                 "--no-playlist","--quiet","--no-warnings",
                 "--get-id", f"ytsearch1:{query}"],
                capture_output=True, text=True, timeout=20)
            vid = r2.stdout.strip().splitlines()[0].strip() if r2.stdout.strip() else ""
            return vid, query
        except Exception:
            return "", ""

    def _open(self, url:str) -> bool:
        if not shutil.which("firefox"):
            return False
        already = subprocess.run(["pgrep","-x","firefox"],
                                  capture_output=True).returncode == 0
        cmd = ["firefox","--new-tab",url] if already else ["firefox",url]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return True

    def _focus(self):
        for cmd in [["hyprctl","dispatch","focuswindow","class:firefox"],
                    ["wmctrl","-a","Firefox"]]:
            try: subprocess.run(cmd, capture_output=True, timeout=2); break
            except Exception: pass
        time.sleep(0.3)

    def _key(self, k:str):
        for tool,args in [("ydotool",["ydotool","key",k]),
                          ("xdotool",["xdotool","key","--clearmodifiers",k])]:
            if shutil.which(tool):
                subprocess.run(args, capture_output=True, timeout=2); return

    def pause_resume(self): self._focus(); self._key("k")
    def mute_video(self):   self._focus(); self._key("m")
    def fullscreen(self):   self._focus(); self._key("f")
PY
ok "core/youtube_ctrl.py"

# ───────────────────────────────────────────────────────
# core/task_engine.py — THE GATEKEEPER
# ───────────────────────────────────────────────────────
cat > "$DIR/core/task_engine.py" << 'PY'
"""
Luna Task Engine — runs BEFORE AI, every single time.
Returns TaskResult → AI is SKIPPED.
Returns None       → AI runs.
"""
import os, re, subprocess, sys
from pathlib import Path
from core.system_ctrl  import BrightnessCtrl, VolumeCtrl
from core.youtube_ctrl import YouTubeController


class TaskResult:
    def __init__(self, success:bool, message:str, output:str=""):
        self.success = success
        self.message = message
        self.output  = output


class TaskEngine:
    def __init__(self, mem):
        self.mem  = mem
        self._br  = BrightnessCtrl()
        self._vol = VolumeCtrl()
        self._yt  = YouTubeController()

    @property
    def workspace(self) -> Path:
        d = Path(self.mem.get("workspace_dir", str(Path.home()/"LunaWorkspace")))
        d.mkdir(parents=True, exist_ok=True); return d

    @property
    def music_dir(self) -> Path:
        d = Path(self.mem.get("download_dir", str(Path.home()/"Music")))
        d.mkdir(parents=True, exist_ok=True); return d

    def handle(self, raw:str):
        # Strip wake word prefix
        t  = raw.strip()
        tl = t.lower()
        for ww in ("luna, ","luna ","hey luna, ","hey luna "):
            if tl.startswith(ww):
                tl = tl[len(ww):].strip()
                t  = t[len(ww):].strip()
                break

        # ── BRIGHTNESS ────────────────────────────────────
        bc = self._br_parse(tl)
        if bc: return self._br_run(bc)

        # ── VOLUME ────────────────────────────────────────
        vc = self._vol_parse(tl)
        if vc: return self._vol_run(vc)

        # ── YOUTUBE controls ─────────────────────────────
        if re.search(r"\b(pause|resume)\b",tl) and re.search(r"\b(video|youtube|song|music)\b",tl):
            self._yt.pause_resume()
            return TaskResult(True,"YouTube paused/resumed.")

        if re.search(r"\bmute\b",tl) and re.search(r"\b(video|youtube)\b",tl):
            self._yt.mute_video()
            return TaskResult(True,"YouTube muted.")

        # ── PLAY → YouTube ────────────────────────────────
        m = re.search(
            r"^(?:play|put on|start|open|watch|search|find)\s+"
            r"(?:the\s+)?(?:song|video|music|track|audio\s+)?"
            r"(.+?)(?:\s+on\s+(?:youtube|yt|firefox))?\s*$",
            t, re.IGNORECASE)
        if m:
            q = m.group(1).strip()
            # Don't intercept pure control words
            if not re.match(r"^(volume|brightness|bright|screen|mute|unmute)\b", q.lower()):
                ok, msg = self._yt.search_and_play(q)
                return TaskResult(ok, msg, output=f"YouTube: {q}")

        # ── DOWNLOAD mp3 ──────────────────────────────────
        m = re.search(r"^download\s+(?:song|music|audio|track\s+)?(.+)$", t, re.IGNORECASE)
        if m: return self._dl_mp3(m.group(1).strip())

        # ── SHELL ─────────────────────────────────────────
        m = re.search(r"^(?:run|execute|shell|cmd|bash|sudo)\s+(.+)$", t, re.IGNORECASE)
        if m: return self._shell(m.group(1))

        # ── INSTALL ───────────────────────────────────────
        m = re.search(r"^install\s+(?:package\s+)?(\S+)", tl)
        if m: return self._install(m.group(1))

        # ── CREATE DIR ────────────────────────────────────
        m = re.search(r"create\s+(?:a\s+)?(?:dir(?:ectory)?|folder)\s+(?:called?|named?)?\s*['\"]?(\S+)['\"]?", tl)
        if m: return self._mkdir(m.group(1))

        # ── CREATE FILE ───────────────────────────────────
        m = re.search(r"create\s+(?:a\s+)?file\s+(?:called?|named?)?\s*['\"]?([\w.\-]+)['\"]?", tl)
        if m: return self._touch(m.group(1))

        # ── LIST ──────────────────────────────────────────
        if re.search(r"^(?:list|ls|show)\s+(?:files?|workspace)", tl):
            return self._ls()

        # ── STATUS ────────────────────────────────────────
        if re.search(r"(?:brightness|volume|sound)\s+(?:status|level|current|how much)", tl):
            b = self._br.get(); v = self._vol.get()
            parts = []
            if b >= 0: parts.append(f"Brightness: {b}%")
            if v >= 0: parts.append(f"Volume: {v}%")
            return TaskResult(True, " | ".join(parts) or "Could not read levels.")

        return None  # → AI runs

    # ── Brightness parser ─────────────────────────────────────────────────
    def _br_parse(self, tl):
        if not re.search(r"\b(bright(?:ness)?|screen|display|backlight|dim|monitor)\b", tl):
            return None
        if re.search(r"\b(max(?:imum)?|full|100)\b",         tl): return {"a":"max"}
        if re.search(r"\b(min(?:imum)?|lowest|very\s*low|dark|minimum)\b", tl): return {"a":"min"}
        if re.search(r"\b(up|increase|brighter|higher|raise|more|boost)\b", tl):
            m = re.search(r"(\d+)",tl)
            return {"a":"up","s": min(int(m.group(1)),100) if m else 10}
        if re.search(r"\b(down|decrease|dim(?:mer)?|lower|reduce|less|darker)\b", tl):
            m = re.search(r"(\d+)",tl)
            return {"a":"down","s": min(int(m.group(1)),100) if m else 10}
        m = re.search(r"(\d{1,3})\s*%?", tl)
        if m: return {"a":"set","v": min(int(m.group(1)),100)}
        return None

    def _br_run(self, c) -> TaskResult:
        if not self._br.available():
            return TaskResult(False,
                "brightnessctl not installed.\n"
                "Fix: sudo pacman -S brightnessctl\n"
                "     sudo usermod -aG video $USER\n"
                "     (then re-login)")
        a = c["a"]
        if   a=="max":  ok,msg = self._br.max_b()
        elif a=="min":  ok,msg = self._br.min_b()
        elif a=="up":   ok,msg = self._br.up(c.get("s",10))
        elif a=="down": ok,msg = self._br.down(c.get("s",10))
        elif a=="set":  ok,msg = self._br.set_pct(c.get("v",50))
        else: return TaskResult(False,"Unknown brightness command.")
        return TaskResult(ok, msg)

    # ── Volume parser ──────────────────────────────────────────────────────
    def _vol_parse(self, tl):
        # Mic
        if re.search(r"\b(mic|microphone)\b", tl):
            if "unmute" in tl: return {"a":"mic_unmute"}
            if "mute"   in tl: return {"a":"mic_mute"}
        # Unmute / mute
        if re.search(r"\bunmute\b", tl): return {"a":"unmute"}
        if re.search(r"\bmute\b",   tl) and not re.search(r"\b(youtube|video)\b",tl):
            return {"a":"mute"}
        # Max / min via natural language
        if re.search(r"\b(vol(?:ume)?|sound|audio)\b", tl):
            if re.search(r"\b(max(?:imum)?|full|100|loudest)\b",   tl): return {"a":"set","v":100}
            if re.search(r"\b(min(?:imum)?|zero|silent|quietest)\b",tl): return {"a":"set","v":0}
        # Up
        if re.search(r"\b(vol(?:ume)?\s*up|louder|increase\s*(?:the\s*)?vol|"
                     r"raise\s*(?:the\s*)?vol|turn\s*(?:it\s*|the\s*vol\s*)?up|"
                     r"sound\s*up|audio\s*up)\b", tl):
            m = re.search(r"(\d+)", tl)
            return {"a":"up","s": min(int(m.group(1)),100) if m and int(m.group(1))<=100 else 10}
        # Down
        if re.search(r"\b(vol(?:ume)?\s*down|quieter|decrease\s*(?:the\s*)?vol|"
                     r"lower\s*(?:the\s*)?vol|turn\s*(?:it\s*|the\s*vol\s*)?down|"
                     r"sound\s*down|audio\s*down)\b", tl):
            m = re.search(r"(\d+)", tl)
            return {"a":"down","s": min(int(m.group(1)),100) if m and int(m.group(1))<=100 else 10}
        # Set exact: "set volume to 60" / "volume 60%" / "volume at 60"
        m = re.search(r"(?:set\s+)?(?:vol(?:ume)?|sound|audio)\s+(?:to\s+|at\s+)?(\d{1,3})\s*%?", tl)
        if m: return {"a":"set","v": min(int(m.group(1)),150)}
        return None

    def _vol_run(self, c) -> TaskResult:
        if not self._vol.available():
            return TaskResult(False,
                "wpctl/pactl not found.\n"
                "Fix: sudo pacman -S pipewire pipewire-pulse wireplumber")
        a = c["a"]
        if   a=="mute":       ok,msg = self._vol.mute()
        elif a=="unmute":     ok,msg = self._vol.unmute()
        elif a=="up":         ok,msg = self._vol.up(c.get("s",10))
        elif a=="down":       ok,msg = self._vol.down(c.get("s",10))
        elif a=="set":        ok,msg = self._vol.set_pct(c.get("v",50))
        elif a=="mic_mute":   ok,msg = self._vol.mic_mute()
        elif a=="mic_unmute": ok,msg = self._vol.mic_unmute()
        else: return TaskResult(False,"Unknown volume command.")
        return TaskResult(ok, msg)

    # ── Download mp3 ───────────────────────────────────────────────────────
    def _dl_mp3(self, query) -> TaskResult:
        try: import yt_dlp
        except ImportError:
            subprocess.run([sys.executable,"-m","pip","install","yt-dlp","-q"],
                           capture_output=True, timeout=60)
        out = str(self.music_dir/"%(title)s.%(ext)s")
        try:
            r = subprocess.run(
                [sys.executable,"-m","yt_dlp",
                 f"ytsearch1:{query}",
                 "--extract-audio","--audio-format","mp3","--audio-quality","0",
                 "-o",out,"--no-playlist",
                 "--print","after_move:filepath","--no-warnings"],
                capture_output=True, text=True, timeout=120)
            path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
            if not path or not Path(path).exists():
                files = sorted(self.music_dir.glob("*.mp3"),key=os.path.getmtime,reverse=True)
                path = str(files[0]) if files else ""
            if not path:
                return TaskResult(False,f"Download failed: {(r.stderr or r.stdout)[:300]}")
            return TaskResult(True,f"Downloaded: {Path(path).name}",output=f"Saved: {path}")
        except subprocess.TimeoutExpired:
            return TaskResult(False,"Download timed out.")
        except Exception as e:
            return TaskResult(False,f"Download error: {e}")

    # ── Misc ───────────────────────────────────────────────────────────────
    def _mkdir(self, name):
        try:
            t = self.workspace/name; t.mkdir(parents=True,exist_ok=True)
            return TaskResult(True,f"Created directory: {t}")
        except Exception as e: return TaskResult(False,str(e))

    def _touch(self, name, content=""):
        try:
            t = self.workspace/name
            t.parent.mkdir(parents=True,exist_ok=True); t.write_text(content)
            return TaskResult(True,f"Created file: {t}",output=str(t))
        except Exception as e: return TaskResult(False,str(e))

    def write_code(self, filename, code, lang=""):
        ext={"python":"py","py":"py","javascript":"js","js":"js",
             "bash":"sh","sh":"sh","html":"html","css":"css","rust":"rs"}
        if "." not in filename: filename += "."+ext.get(lang.lower(),"txt")
        try:
            t = self.workspace/filename
            t.parent.mkdir(parents=True,exist_ok=True); t.write_text(code)
            if filename.endswith(".sh"): os.chmod(t,0o755)
            return TaskResult(True,f"Saved: {t}",output=str(t))
        except Exception as e: return TaskResult(False,str(e))

    def _shell(self, cmd):
        try:
            r = subprocess.run(cmd,shell=True,capture_output=True,text=True,
                               timeout=60,cwd=str(self.workspace),env={**os.environ})
            out=(r.stdout+r.stderr).strip(); ok=r.returncode==0
            return TaskResult(ok,f"Exit {r.returncode}.",output=out or "(no output)")
        except subprocess.TimeoutExpired: return TaskResult(False,"Timed out.")
        except Exception as e: return TaskResult(False,str(e))

    def _install(self, pkg):
        for cmd in [[sys.executable,"-m","pip","install",pkg,"-q"],
                    ["sudo","pacman","-S",pkg,"--noconfirm"],
                    ["yay","-S",pkg,"--noconfirm"]]:
            try:
                r = subprocess.run(cmd,capture_output=True,text=True,timeout=120)
                if r.returncode==0: return TaskResult(True,f"Installed `{pkg}`.")
            except (FileNotFoundError,subprocess.TimeoutExpired): continue
        return TaskResult(False,f"Could not install `{pkg}`.")

    def _ls(self):
        files=list(self.workspace.rglob("*"))
        if not files: return TaskResult(True,"Workspace is empty.")
        lines=[f"{'📁' if f.is_dir() else '📄'} {f.relative_to(self.workspace)}"
               for f in sorted(files)[:50]]
        return TaskResult(True,f"{len(files)} items:",output="\n".join(lines))
PY
ok "core/task_engine.py"

# ───────────────────────────────────────────────────────
# core/ai_engine.py — bulletproof system prompt
# ───────────────────────────────────────────────────────
cat > "$DIR/core/ai_engine.py" << 'PY'
"""Luna AI Engine — NEVER fakes system tasks"""
import re, psutil
from datetime import datetime
from pathlib import Path

# The AI will NEVER see "play", "volume", "brightness" commands
# because task_engine intercepts them first.
# This prompt is a last line of defense.
SYSTEM_PROMPT = """You are Luna, an AI assistant on Arch Linux + Hyprland.

HARD RULES — BREAKING THESE IS NOT ALLOWED:
1. You have NO ability to play music, open browsers, control volume, or change brightness.
   A hardware task engine handles those before you are called.
   If the user asked you to do a system action, it ALREADY HAPPENED.
   Say only: "Done." or confirm the action in 1 short sentence.
2. FORBIDDEN PHRASES — never say these:
   - "I'll play..."  "I will play..."  "Starting playback..."
   - "I'll open Firefox..."  "Opening YouTube..."
   - "I'll download..."  "Downloading..."
   - "I'll set the volume..."  "Adjusting volume..."
   - "I'll change brightness..."
   - "I accessed the music library"
   - "Playing in the background"
3. Keep all replies SHORT: 1-3 sentences max.
4. For code: wrap in ```language\n...\n``` fences.
5. Plain text only in speech — no **, *, or # markdown.
6. You are on Arch Linux. Use pacman/yay, wpctl, brightnessctl, hyprctl.
"""


class AIEngine:
    def __init__(self, mem):
        self.mem = mem

    @property
    def provider(self):     return self.mem.get("provider",     "gemini")
    @property
    def model(self):        return self.mem.get("model",        "gemini-2.0-flash")
    @property
    def api_key(self):      return self.mem.get("api_key",      "")
    @property
    def groq_key(self):     return self.mem.get("groq_api_key", "")
    @property
    def ollama_model(self): return self.mem.get("ollama_model", "llama3")

    def _ctx(self):
        try:
            cpu  = psutil.cpu_percent(interval=0.1)
            ram  = psutil.virtual_memory()
            now  = datetime.now().strftime("%A %B %d %Y, %I:%M %p")
            user = self.mem.get_user_name() or "User"
            return (f"[Arch+Hyprland | {now} | CPU {cpu:.0f}% | "
                    f"RAM {ram.percent:.0f}% | User:{user}]")
        except Exception:
            return "[Arch Linux + Hyprland]"

    def process(self, text:str, history=None) -> str:
        tl = text.lower().strip()
        if re.fullmatch(r"(hi|hello|hey|yo|sup|hiya)", tl):
            n = self.mem.get_user_name()
            return f"Hey{' '+n if n else ''}! What do you need?"
        if m := re.search(r"my name is (.+)", tl):
            name = m.group(1).strip().title()
            self.mem.set_user_name(name)
            return f"Got it, I'll remember you as {name}."
        if re.fullmatch(r"(time|what.?s the time|current time)", tl):
            return datetime.now().strftime("It's %I:%M %p.")
        if re.fullmatch(r"(date|today|what.?s the date|current date)", tl):
            return datetime.now().strftime("Today is %A, %B %d, %Y.")
        if "clear" in tl and ("chat" in tl or "history" in tl):
            self.mem.clear_history(); return "Chat cleared."

        if self.provider == "gemini":  return self._gemini(text, history)
        if self.provider == "groq":    return self._groq(text, history)
        if self.provider == "ollama":  return self._ollama(text)
        return "No AI provider set. Open Settings ⚙."

    def _gemini(self, text, history):
        if not self.api_key: return "Gemini API key not set. Open Settings ⚙."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            ctx = [SYSTEM_PROMPT, self._ctx(), ""]
            if history:
                for h in history[-10:]:
                    ctx.append(f"{'User' if h['role']=='user' else 'Luna'}: {h['content']}")
            ctx.append(f"User: {text}\nLuna:")
            r = client.models.generate_content(model=self.model, contents="\n".join(ctx))
            return r.text.strip()
        except ImportError: return "Install: pip install google-genai"
        except Exception as e: return f"Gemini error: {str(e)[:200]}"

    def _groq(self, text, history):
        if not self.groq_key: return "Groq API key not set. Open Settings ⚙."
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            msgs = [{"role":"system","content":SYSTEM_PROMPT+"\n"+self._ctx()}]
            if history:
                for h in history[-10:]:
                    msgs.append({"role":h["role"],"content":h["content"]})
            msgs.append({"role":"user","content":text})
            r = client.chat.completions.create(
                model=self.model, messages=msgs, max_tokens=800, temperature=0.6)
            return r.choices[0].message.content.strip()
        except ImportError: return "Install: pip install groq"
        except Exception as e: return f"Groq error: {str(e)[:200]}"

    def _ollama(self, text):
        try:
            import requests
            r = requests.post("http://localhost:11434/api/generate",
                json={"model":self.ollama_model,
                      "prompt":f"{SYSTEM_PROMPT}\n{self._ctx()}\nUser:{text}\nLuna:",
                      "stream":False}, timeout=60)
            return r.json().get("response","").strip() if r.ok else f"Ollama {r.status_code}"
        except Exception as e: return f"Ollama error: {str(e)[:120]}"

    @staticmethod
    def gemini_models():
        return [("gemini-2.0-flash","Gemini 2.0 Flash ★"),
                ("gemini-2.0-flash-thinking-exp-01-21","Gemini 2.0 Flash Thinking"),
                ("gemini-1.5-pro","Gemini 1.5 Pro"),
                ("gemini-1.5-flash","Gemini 1.5 Flash")]

    @staticmethod
    def groq_models():
        return [("llama-3.3-70b-versatile","LLaMA 3.3 70B ★"),
                ("llama-3.1-8b-instant","LLaMA 3.1 8B"),
                ("mixtral-8x7b-32768","Mixtral 8x7B"),
                ("gemma2-9b-it","Gemma 2 9B"),
                ("deepseek-r1-distill-llama-70b","DeepSeek R1 70B")]
PY
ok "core/ai_engine.py"

# ───────────────────────────────────────────────────────
# ui/main_window.py — TASK ENGINE ALWAYS RUNS FIRST
# The previous bug: send() was sometimes calling AI directly
# ───────────────────────────────────────────────────────
cat > "$DIR/ui/main_window.py" << 'PY'
"""
Luna AI v5 Main Window
CRITICAL FIX: send() ALWAYS goes → TaskThread first
              AI is only called if TaskThread returns None
"""
from datetime import datetime
try:
    from PyQt6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
                                  QLabel,QPushButton,QScrollArea,QLineEdit,QFrame)
    from PyQt6.QtCore  import Qt,QTimer,QThread,pyqtSignal
    from PyQt6.QtGui   import QFont
    _SF  = Qt.FocusPolicy.StrongFocus
    _WW  = Qt.TextInteractionFlag.TextSelectableByMouse
    _AOF = Qt.ScrollBarPolicy.AlwaysOff
except ImportError:
    from PyQt5.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
                                  QLabel,QPushButton,QScrollArea,QLineEdit,QFrame)
    from PyQt5.QtCore  import Qt,QTimer,QThread,pyqtSignal
    from PyQt5.QtGui   import QFont
    _SF=Qt.StrongFocus; _WW=Qt.TextSelectableByMouse; _AOF=Qt.AlwaysOff

from ui.widgets        import StatusDot,HUDWidget,VoiceVisualizer,SystemMeter
from ui.code_block     import CodeBlockWidget
from ui.settings_panel import SettingsPanel
from core.code_parser  import parse_response

try:
    from core.wake_word import WakeWordEngine
    _HAS_WAKE = True
except Exception:
    _HAS_WAKE = False


class _TaskThread(QThread):
    done = pyqtSignal(object)
    def __init__(self, te, text):
        super().__init__(); self.te=te; self.text=text
    def run(self): self.done.emit(self.te.handle(self.text))


class _AIThread(QThread):
    done  = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, ai, text, history):
        super().__init__(); self.ai=ai; self.text=text; self.history=history
    def run(self):
        try:    self.done.emit(self.ai.process(self.text, self.history))
        except Exception as e: self.error.emit(str(e))


class _MicThread(QThread):
    done  = pyqtSignal(str)
    error = pyqtSignal(str)
    def run(self):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.4)
                audio = r.listen(src, timeout=8, phrase_time_limit=14)
            self.done.emit(r.recognize_google(audio))
        except ImportError: self.error.emit("__import__")
        except Exception as e: self.error.emit(str(e))


def _bubble(text:str, role:str) -> QWidget:
    w = QWidget(); lay = QHBoxLayout(w); lay.setContentsMargins(0,2,0,2)
    b = QLabel(text); b.setWordWrap(True); b.setTextInteractionFlags(_WW)
    tbl = {"user":("bubbleUser",True),"ai":("bubbleAI",False),
           "system":("bubbleSystem",False),"task_ok":("bubbleTaskOk",False),
           "task_err":("bubbleTaskErr",False)}
    obj, right = tbl.get(role,("bubbleSystem",False))
    b.setObjectName(obj); b.setMaximumWidth(600)
    (lay.addStretch(),lay.addWidget(b)) if right else (lay.addWidget(b),lay.addStretch())
    return w


class MainWindow(QMainWindow):
    def __init__(self, voice, ai, mem, task_engine):
        super().__init__()
        self.voice=voice; self.ai=ai; self.mem=mem; self.te=task_engine
        self._tt=self._at=self._mt=None
        self._pending=""
        self.setWindowTitle("LUNA AI  v5"); self.setMinimumSize(1020,730); self.resize(1260,860)
        self._build(); self._wire()
        QTimer.singleShot(0, self._clock_tick)

        # Wake word (optional)
        self._wake = None
        if _HAS_WAKE:
            try:
                self._wake = WakeWordEngine(self)
                self._wake.wake_detected.connect(self._on_wake)
                self._wake.command_heard.connect(self._on_wake_cmd)
                self._wake.status_changed.connect(self._on_wake_status)
                self._wake.start()
            except Exception:
                self._wake = None

    # ─── UI build ─────────────────────────────────────────────────────────
    def _build(self):
        root=QWidget(); self.setCentralWidget(root)
        vb=QVBoxLayout(root); vb.setContentsMargins(0,0,0,0); vb.setSpacing(0)
        vb.addWidget(self._mk_header())
        body=QWidget(); body.setObjectName("bodyArea")
        hb=QHBoxLayout(body); hb.setContentsMargins(14,12,14,12); hb.setSpacing(14)
        hb.addWidget(self._mk_left()); hb.addWidget(self._mk_chat(),1)
        vb.addWidget(body,1); vb.addWidget(self._mk_input())

    def _mk_header(self):
        bar=QFrame(); bar.setObjectName("headerBar"); bar.setFixedHeight(56)
        lay=QHBoxLayout(bar); lay.setContentsMargins(20,0,20,0); lay.setSpacing(0)
        self.status_dot=StatusDot()
        logo=QLabel("L·U·N·A"); logo.setObjectName("logoLabel")
        sub=QLabel("  AI v5");  sub.setObjectName("subLabel")
        self.status_text=QLabel("BOOTING"); self.status_text.setObjectName("statusText")
        self.wake_lbl=QLabel("🎙 SAY LUNA"); self.wake_lbl.setObjectName("wakeLbl")
        lay.addWidget(self.status_dot); lay.addSpacing(10)
        lay.addWidget(logo); lay.addWidget(sub); lay.addSpacing(16)
        lay.addWidget(self.status_text); lay.addSpacing(18)
        lay.addWidget(self.wake_lbl); lay.addStretch()
        self.time_lbl=QLabel(); self.time_lbl.setObjectName("timeLabel")
        lay.addWidget(self.time_lbl); lay.addSpacing(16)
        for label,attr in [("✕ Clear","clear_btn"),("⏹ Stop","stop_btn"),("⚙ Settings","settings_btn")]:
            b=QPushButton(label); b.setObjectName("headerBtn"); b.setFixedHeight(32)
            setattr(self,attr,b); lay.addSpacing(6); lay.addWidget(b)
        return bar

    def _mk_left(self):
        w=QWidget(); w.setObjectName("leftPanel"); w.setFixedWidth(234)
        lay=QVBoxLayout(w); lay.setContentsMargins(0,0,0,0); lay.setSpacing(10)
        self.hud=HUDWidget(); self.hud.setMinimumHeight(200); lay.addWidget(self.hud)
        self.viz=VoiceVisualizer(); lay.addWidget(self.viz)
        self.meters=SystemMeter(); lay.addWidget(self.meters)
        card=QFrame(); card.setObjectName("infoCard")
        cl=QVBoxLayout(card); cl.setContentsMargins(10,8,10,8); cl.setSpacing(4)
        self.inf_p=QLabel(); self.inf_v=QLabel(); self.inf_u=QLabel(); self.inf_w=QLabel()
        for x in (self.inf_p,self.inf_v,self.inf_u,self.inf_w):
            x.setObjectName("infoLine"); x.setWordWrap(True); cl.addWidget(x)
        lay.addWidget(card); lay.addStretch(); self._refresh_info()
        return w

    def _mk_chat(self):
        frame=QFrame(); frame.setObjectName("chatPanel")
        lay=QVBoxLayout(frame); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        hdr=QLabel("  CONVERSATION"); hdr.setObjectName("chatHeader"); hdr.setFixedHeight(36)
        lay.addWidget(hdr)
        div=QFrame(); div.setObjectName("divider"); div.setFixedHeight(1); lay.addWidget(div)
        self._scroll=QScrollArea(); self._scroll.setObjectName("chatScroll")
        self._scroll.setWidgetResizable(True); self._scroll.setHorizontalScrollBarPolicy(_AOF)
        self._mc=QWidget(); self._mc.setObjectName("msgContainer")
        self._ml=QVBoxLayout(self._mc)
        self._ml.setContentsMargins(14,10,14,10); self._ml.setSpacing(6); self._ml.addStretch()
        self._scroll.setWidget(self._mc); lay.addWidget(self._scroll,1)
        return frame

    def _mk_input(self):
        bar=QFrame(); bar.setObjectName("inputBar"); bar.setFixedHeight(68)
        lay=QHBoxLayout(bar); lay.setContentsMargins(16,12,16,12); lay.setSpacing(10)
        self.mic_btn=QPushButton("🎙"); self.mic_btn.setObjectName("micBtn"); self.mic_btn.setFixedSize(44,44)
        self.inp=QLineEdit(); self.inp.setObjectName("inputField"); self.inp.setFocusPolicy(_SF)
        self.inp.setPlaceholderText(
            'Say "Luna" or type: play song X  ·  volume up  ·  brightness 70%  ·  mute')
        self.send_btn=QPushButton("SEND  ↵"); self.send_btn.setObjectName("sendBtn"); self.send_btn.setFixedSize(110,44)
        lay.addWidget(self.mic_btn); lay.addWidget(self.inp,1); lay.addWidget(self.send_btn)
        return bar

    def _wire(self):
        self.send_btn.clicked.connect(self.send)
        self.inp.returnPressed.connect(self.send)
        self.settings_btn.clicked.connect(self._settings)
        self.clear_btn.clicked.connect(self._clear)
        self.stop_btn.clicked.connect(self._stop)
        self.mic_btn.clicked.connect(self._mic)
        t=QTimer(self); t.timeout.connect(self._clock_tick); t.start(1000)

    def _clock_tick(self):
        self.time_lbl.setText(datetime.now().strftime("%H:%M:%S"))

    def set_status(self, s:str):
        self.status_text.setText(s); self.status_dot.set_state(s); self.hud.set_state(s)
        self.viz.start() if s in ("SPEAKING","THINKING","LISTENING","WORKING") else self.viz.stop()

    def _refresh_info(self):
        import os
        p=self.mem.get("provider","?").upper(); m=self.mem.get("model","—").split("-")[-1]
        v=self.mem.get("voice","—").replace("Neural","").replace("-"," ").strip()
        u=self.mem.get_user_name() or "—"; ws=self.mem.get("workspace_dir","—")
        self.inf_p.setText(f"◈ {p} · {m}"); self.inf_v.setText(f"◈ Voice: {v}")
        self.inf_u.setText(f"◈ User: {u}"); self.inf_w.setText(f"◈ WS: ~/{os.path.basename(ws)}")

    def _add(self, text, role):
        w=_bubble(text,role); self._ml.insertWidget(self._ml.count()-1,w)
        QTimer.singleShot(30,self._scroll_end)

    def _add_code(self, code, lang, idx):
        w=CodeBlockWidget(code,lang,idx,self.te,self._mc)
        self._ml.insertWidget(self._ml.count()-1,w); QTimer.singleShot(30,self._scroll_end)

    def _add_out(self, text):
        b=QLabel(text); b.setObjectName("taskOutput"); b.setWordWrap(True)
        b.setTextInteractionFlags(_WW); b.setFont(QFont("Consolas",11))
        self._ml.insertWidget(self._ml.count()-1,b); QTimer.singleShot(30,self._scroll_end)

    def _scroll_end(self):
        sb=self._scroll.verticalScrollBar(); sb.setValue(sb.maximum())

    # ─── SEND — task engine ALWAYS first ──────────────────────────────────
    def send(self):
        text = self.inp.text().strip()
        if not text: return
        self.inp.clear(); self._ui(False)
        self._add(text,"user"); self.mem.add_to_history("user",text)
        self._pending = text
        self.set_status("WORKING")
        # ↓↓↓ ALWAYS goes to TaskThread first — never directly to AI ↓↓↓
        self._tt = _TaskThread(self.te, text)
        self._tt.done.connect(self._task_done)
        self._tt.start()

    def _task_done(self, result):
        """Called when task engine finishes. result=None means → call AI."""
        if result is not None:
            # Task engine handled it — show result, SKIP AI entirely
            icon = "✓" if result.success else "✗"
            self._add(f"{icon} {result.message}", "task_ok" if result.success else "task_err")
            if result.output: self._add_out(result.output)
            self._ui(True); self.set_status("SPEAKING")
            speak = result.message.replace("`","").replace("*","").replace("#","")
            if self._wake: self._wake.pause()
            self.voice.speak_async(speak, on_done=lambda:(
                self.set_status("READY"),
                self._wake.resume() if self._wake else None))
        else:
            # No task matched → now call AI
            self.set_status("THINKING")
            self._at = _AIThread(self.ai, self._pending, self.mem.get_history()[:-1])
            self._at.done.connect(self._ai_done)
            self._at.error.connect(self._ai_err)
            self._at.start()

    def _ai_done(self, resp:str):
        self.mem.add_to_history("assistant",resp)
        parsed = parse_response(resp)
        if parsed.explanation.strip(): self._add(parsed.explanation,"ai")
        for cb in parsed.code_blocks: self._add_code(cb.code,cb.language,cb.index)
        self._ui(True); self.set_status("SPEAKING")
        tts = parsed.explanation if parsed.explanation else "Done."
        if self._wake: self._wake.pause()
        self.voice.speak_async(tts, on_done=lambda:(
            self.set_status("READY"),
            self._wake.resume() if self._wake else None))

    def _ai_err(self, e:str):
        self._add(f"AI error: {e}","system"); self._ui(True); self.set_status("READY")

    def _ui(self, on:bool):
        self.inp.setEnabled(on); self.send_btn.setEnabled(on)
        if on: self.inp.setFocus()

    # ─── Wake word ─────────────────────────────────────────────────────────
    def _on_wake(self):
        self.set_status("LISTENING"); self.wake_lbl.setText("🔴 LISTENING…")
        self._add("Listening…","system")
        if self._wake: self._wake.pause()
        self.voice.speak_async("Yes?", on_done=lambda: self._wake.resume() if self._wake else None)

    def _on_wake_cmd(self, text:str):
        self.wake_lbl.setText("🎙 SAY LUNA"); self.inp.setText(text); self.send()

    def _on_wake_status(self, s:str):
        m={"idle":"🎙 SAY LUNA","awake":"🔴 LISTENING…","listening":"🎤 SPEAK NOW"}
        self.wake_lbl.setText(m.get(s,"🎙 SAY LUNA"))

    # ─── Mic button ────────────────────────────────────────────────────────
    def _mic(self):
        self.mic_btn.setEnabled(False); self.set_status("LISTENING")
        self._mt=_MicThread()
        self._mt.done.connect(self._mic_ok); self._mt.error.connect(self._mic_err)
        self._mt.start()

    def _mic_ok(self, text:str):
        self.mic_btn.setEnabled(True); self.inp.setText(text); self.set_status("READY"); self.send()

    def _mic_err(self, e:str):
        self.mic_btn.setEnabled(True); self.set_status("READY")
        self._add("Install: pip install SpeechRecognition pyaudio" if e=="__import__"
                  else f"Mic error: {e}", "system")

    # ─── Misc ──────────────────────────────────────────────────────────────
    def _settings(self):
        dlg=SettingsPanel(self.mem,self.voice,self); dlg.settings_saved.connect(self._refresh_info); dlg.exec()

    def _stop(self):
        self.voice.stop()
        for t in (self._tt,self._at,self._mt):
            if t and t.isRunning(): t.terminate()
        self._ui(True); self.set_status("READY")

    def _clear(self):
        while self._ml.count()>1:
            item=self._ml.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.mem.clear_history(); self._add("Cleared.","system")

    def greet(self):
        user=self.mem.get_user_name()
        msg=(f"Welcome back {user}. Luna online. Say 'Luna' to wake me." if user
             else "Luna online. Open Settings to add your API key. Say 'Luna' to wake me.")
        self._add(msg,"ai"); self.set_status("SPEAKING")
        if self._wake: self._wake.pause()
        self.voice.speak_async(msg, on_done=lambda:(
            self.set_status("READY"),
            self._wake.resume() if self._wake else None))

    def closeEvent(self, e):
        if self._wake: self._wake.stop_engine(); self._wake.wait(1000)
        super().closeEvent(e)
PY
ok "ui/main_window.py"

# ───────────────────────────────────────────────────────
# STEP 3: Self-test
# ───────────────────────────────────────────────────────
echo ""
inf "Running self-test..."
echo ""
"$PYTHON" << 'PYTEST'
import sys; sys.path.insert(0,".")

from core.system_ctrl import BrightnessCtrl, VolumeCtrl
from core.memory      import MemoryManager
from core.task_engine import TaskEngine

br  = BrightnessCtrl()
vol = VolumeCtrl()
mem = MemoryManager()
te  = TaskEngine(mem)

print("  BRIGHTNESS:")
print(f"    available : {br.available()}")
print(f"    current   : {br.get()}%")

print("  VOLUME:")
print(f"    available : {vol.available()}")
print(f"    current   : {vol.get()}%")

print("  TASK ENGINE dispatch test:")
cases = [
    ("play believer by imagine dragons",   True,  "YouTube"),
    ("play lo fi hip hop",                 True,  "YouTube"),
    ("volume up",                          True,  "Volume"),
    ("volume down 30",                     True,  "Volume"),
    ("set volume to 50",                   True,  "Volume"),
    ("volume 70%",                         True,  "Volume"),
    ("mute",                               True,  "Volume"),
    ("unmute",                             True,  "Volume"),
    ("brightness up",                      True,  "Brightness"),
    ("brightness down 20",                 True,  "Brightness"),
    ("brightness 60%",                     True,  "Brightness"),
    ("set brightness to 80",               True,  "Brightness"),
    ("dim the screen",                     True,  "Brightness"),
    ("full brightness",                    True,  "Brightness"),
    ("what is quantum computing",          False, "→AI"),
]
all_pass = True
for cmd, should_intercept, label in cases:
    r = te.handle(cmd)
    intercepted = r is not None
    ok = intercepted == should_intercept
    if not ok: all_pass = False
    sym = "✓" if ok else "✗ FAIL"
    print(f"    [{sym}] [{label}] '{cmd}'")

print()
print("  " + ("ALL TESTS PASSED ✓" if all_pass else "SOME TESTS FAILED — check regex"))
PYTEST

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║  DONE. Run: python main.py                 ║"
echo "  ╠══════════════════════════════════════════════╣"
echo "  ║  EXACT PHRASES TO TEST:                    ║"
echo "  ║                                            ║"
echo "  ║  play believer by imagine dragons          ║"
echo "  ║  play lo fi hip hop                        ║"
echo "  ║  download song shape of you               ║"
echo "  ║                                            ║"
echo "  ║  volume up                                 ║"
echo "  ║  volume down 30                            ║"
echo "  ║  volume 70%                                ║"
echo "  ║  mute  /  unmute                           ║"
echo "  ║                                            ║"
echo "  ║  brightness up                             ║"
echo "  ║  brightness down 20                        ║"
echo "  ║  brightness 60%                            ║"
echo "  ║  dim the screen                            ║"
echo "  ║  full brightness                           ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""
