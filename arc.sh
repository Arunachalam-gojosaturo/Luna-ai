#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
#   LUNA AI v5 — FINAL FIX: YouTube + Volume + Brightness
#   Arch Linux / Hyprland / PipeWire / Wayland
#
#   cd ~/Music/Luna-AI-v5
#   chmod +x luna_fix_final.sh && ./luna_fix_final.sh
# ═══════════════════════════════════════════════════════════
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo ""
echo "  ╔════════════════════════════════════════════╗"
echo "  ║  LUNA v5 — FINAL FIX SCRIPT              ║"
echo "  ╚════════════════════════════════════════════╝"
echo ""

[ -f "$DIR/.venv/bin/activate" ] && source "$DIR/.venv/bin/activate"
PYTHON="${PYTHON:-python3}"

# ─────────────────────────────────────────────────────────────
#  AUTO-INSTALL MISSING TOOLS
# ─────────────────────────────────────────────────────────────
echo "  [~] Checking dependencies..."

# brightnessctl
if ! command -v brightnessctl &>/dev/null; then
    echo "  [~] Installing brightnessctl..."
    sudo pacman -S --noconfirm brightnessctl
fi
echo "  [✓] brightnessctl: $(brightnessctl | grep 'Current' | tr -s ' ')"

# Add to video group if not already
if ! groups "$USER" | grep -qw video; then
    sudo usermod -aG video "$USER"
    echo "  [!] Added $USER to video group — you must re-login for this to take effect"
    echo "      For NOW run: newgrp video"
    # Apply immediately for this session
    newgrp video 2>/dev/null || true
else
    echo "  [✓] Already in video group"
fi

# pipewire / wpctl
if ! command -v wpctl &>/dev/null; then
    echo "  [~] Installing pipewire..."
    sudo pacman -S --noconfirm pipewire pipewire-pulse wireplumber
fi
echo "  [✓] wpctl volume: $(wpctl get-volume @DEFAULT_AUDIO_SINK@)"

# yt-dlp
$PYTHON -m pip install -q --upgrade yt-dlp 2>/dev/null
echo "  [✓] yt-dlp: $($PYTHON -m yt_dlp --version 2>/dev/null)"

# firefox
command -v firefox &>/dev/null && echo "  [✓] firefox found" || \
    echo "  [!] firefox not found — install: sudo pacman -S firefox"

echo ""

# ─────────────────────────────────────────────────────────────
#  LIVE TEST: brightness
# ─────────────────────────────────────────────────────────────
echo "  [~] Testing brightness control..."
if brightnessctl set +5% 2>/dev/null; then
    echo "  [✓] brightnessctl write: OK"
else
    echo "  [!] brightnessctl write failed — trying with sudo..."
    sudo brightnessctl set +5% 2>/dev/null && \
        echo "  [✓] Works with sudo — will use sudo in task engine" || \
        echo "  [!] Brightness control unavailable"
fi
NEEDS_SUDO_BRIGHT=false
brightnessctl set +0% 2>/dev/null || NEEDS_SUDO_BRIGHT=true

# ─────────────────────────────────────────────────────────────
#  LIVE TEST: volume
# ─────────────────────────────────────────────────────────────
echo "  [~] Testing volume control..."
if wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+ 2>/dev/null; then
    echo "  [✓] wpctl write: OK"
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%- 2>/dev/null
else
    echo "  [!] wpctl failed — check PipeWire is running: systemctl --user status pipewire"
fi

# ─────────────────────────────────────────────────────────────
#  LIVE TEST: yt-dlp video ID lookup
# ─────────────────────────────────────────────────────────────
echo "  [~] Testing yt-dlp video lookup..."
VID=$($PYTHON -m yt_dlp --no-playlist --no-warnings --get-id \
      "ytsearch1:test video" 2>/dev/null | head -1)
if [ -n "$VID" ]; then
    echo "  [✓] yt-dlp lookup works: $VID"
else
    echo "  [!] yt-dlp lookup failed — check internet connection"
fi

echo ""
echo "  [~] Writing fixed Python files..."

# ═══════════════════════════════════════════════════════════
#  core/system_ctrl.py
# ═══════════════════════════════════════════════════════════
cat > "$DIR/core/system_ctrl.py" << 'PYEOF'
"""
Luna System Controller v2 — Arch Linux / Hyprland
Brightness: brightnessctl (falls back to sudo brightnessctl)
Volume:     wpctl (PipeWire) → pactl (PulseAudio) → amixer
"""
import re, subprocess, shutil


def _run(*cmd) -> subprocess.CompletedProcess:
    return subprocess.run(list(cmd), capture_output=True, text=True)


# ══════════════════════════════════════════════
#  BRIGHTNESS
# ══════════════════════════════════════════════
class BrightnessCtrl:

    def _cmd(self, *args) -> tuple[bool, str]:
        """Try brightnessctl, then sudo brightnessctl."""
        r = _run("brightnessctl", *args)
        if r.returncode == 0:
            return True, r.stdout.strip()
        # Try sudo (for users not yet in video group)
        r2 = subprocess.run(
            ["sudo", "-n", "brightnessctl"] + list(args),
            capture_output=True, text=True)
        if r2.returncode == 0:
            return True, r2.stdout.strip()
        return False, r.stderr.strip() or "brightnessctl failed"

    @staticmethod
    def available() -> bool:
        return shutil.which("brightnessctl") is not None

    def get(self) -> int:
        try:
            cur = int(_run("brightnessctl", "get").stdout.strip())
            mx  = int(_run("brightnessctl", "max").stdout.strip())
            return round(cur / mx * 100) if mx else 0
        except Exception:
            try:
                # Fallback: read sysfs directly
                import glob
                devices = glob.glob("/sys/class/backlight/*/")
                if devices:
                    d = devices[0]
                    cur = int(open(d + "brightness").read())
                    mx  = int(open(d + "max_brightness").read())
                    return round(cur / mx * 100)
            except Exception:
                pass
            return -1

    def set_pct(self, pct: int) -> tuple[bool, str]:
        pct = max(1, min(100, pct))
        ok, _ = self._cmd("set", f"{pct}%")
        cur = self.get()
        return ok, (f"Brightness set to {pct}%." if ok
                    else f"Failed. Try: sudo usermod -aG video $USER")

    def up(self, step=10) -> tuple[bool, str]:
        ok, _ = self._cmd("set", f"+{step}%")
        cur = self.get()
        return ok, f"Brightness increased to {cur}%."

    def down(self, step=10) -> tuple[bool, str]:
        ok, _ = self._cmd("set", f"{step}%-")
        cur = self.get()
        return ok, f"Brightness decreased to {cur}%."

    def max_bright(self) -> tuple[bool, str]:
        ok, _ = self._cmd("set", "100%")
        return ok, "Brightness at maximum." if ok else ("Failed to set max.", )

    def min_bright(self) -> tuple[bool, str]:
        ok, _ = self._cmd("set", "5%")
        return ok, "Brightness at minimum." if ok else ("Failed to set minimum.", )


# ══════════════════════════════════════════════
#  VOLUME
# ══════════════════════════════════════════════
class VolumeCtrl:
    SINK = "@DEFAULT_AUDIO_SINK@"
    SRC  = "@DEFAULT_AUDIO_SOURCE@"

    def _wpctl(self, *args) -> subprocess.CompletedProcess:
        return _run("wpctl", *args)

    def _pactl(self, *args) -> subprocess.CompletedProcess:
        return _run("pactl", *args)

    def _amixer(self, *args) -> subprocess.CompletedProcess:
        return _run("amixer", "-q", *args)

    @staticmethod
    def available() -> bool:
        return (shutil.which("wpctl") is not None or
                shutil.which("pactl") is not None or
                shutil.which("amixer") is not None)

    def get(self) -> int:
        # wpctl
        try:
            r = _run("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@")
            # Output: "Volume: 0.65" or "Volume: 0.65 [MUTED]"
            m = re.search(r"Volume:\s*(\d+\.?\d*)", r.stdout)
            if m:
                return int(float(m.group(1)) * 100)
        except Exception:
            pass
        # pactl fallback
        try:
            r = _run("pactl", "get-sink-volume", "@DEFAULT_SINK@")
            m = re.search(r"(\d+)%", r.stdout)
            if m:
                return int(m.group(1))
        except Exception:
            pass
        return -1

    def is_muted(self) -> bool:
        try:
            r = _run("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@")
            return "MUTED" in r.stdout.upper()
        except Exception:
            return False

    def set_pct(self, pct: int) -> tuple[bool, str]:
        pct = max(0, min(150, pct))
        # wpctl uses 0.0–1.5 float
        fval = f"{pct / 100:.2f}"
        r = self._wpctl("set-volume", self.SINK, fval)
        if r.returncode == 0:
            return True, f"Volume set to {pct}%."
        # pactl fallback
        r2 = self._pactl("set-sink-volume", "@DEFAULT_SINK@", f"{pct}%")
        return r2.returncode == 0, f"Volume set to {pct}%."

    def up(self, step=10) -> tuple[bool, str]:
        # wpctl: increase with hard cap at 150%
        r = self._wpctl("set-volume", "-l", "1.5", self.SINK, f"{step}%+")
        if r.returncode != 0:
            self._pactl("set-sink-volume", "@DEFAULT_SINK@", f"+{step}%")
        cur = self.get()
        return True, f"Volume up to {cur}%."

    def down(self, step=10) -> tuple[bool, str]:
        r = self._wpctl("set-volume", self.SINK, f"{step}%-")
        if r.returncode != 0:
            self._pactl("set-sink-volume", "@DEFAULT_SINK@", f"-{step}%")
        cur = self.get()
        return True, f"Volume down to {cur}%."

    def mute(self) -> tuple[bool, str]:
        r = self._wpctl("set-mute", self.SINK, "1")
        if r.returncode != 0:
            self._pactl("set-sink-mute", "@DEFAULT_SINK@", "1")
        return True, "Volume muted."

    def unmute(self) -> tuple[bool, str]:
        r = self._wpctl("set-mute", self.SINK, "0")
        if r.returncode != 0:
            self._pactl("set-sink-mute", "@DEFAULT_SINK@", "0")
        return True, "Volume unmuted."

    def toggle(self) -> tuple[bool, str]:
        muted = self.is_muted()
        return self.unmute() if muted else self.mute()

    def mic_mute(self) -> tuple[bool, str]:
        r = self._wpctl("set-mute", self.SRC, "1")
        return (True, "Microphone muted.") if r.returncode == 0 \
               else (False, "Failed to mute mic.")

    def mic_unmute(self) -> tuple[bool, str]:
        r = self._wpctl("set-mute", self.SRC, "0")
        return (True, "Microphone unmuted.") if r.returncode == 0 \
               else (False, "Failed to unmute mic.")
PYEOF
echo "  [✓] core/system_ctrl.py"

# ═══════════════════════════════════════════════════════════
#  core/youtube_ctrl.py  — reliable yt-dlp + Firefox
# ═══════════════════════════════════════════════════════════
cat > "$DIR/core/youtube_ctrl.py" << 'PYEOF'
"""
Luna YouTube Controller v2 — Arch / Hyprland / Wayland
1. yt-dlp --get-id to find YouTube video ID
2. Open https://www.youtube.com/watch?v=ID in Firefox
3. Use ydotool (Wayland) for keyboard shortcuts
"""
import subprocess, shutil, sys, re, time, urllib.parse


class YouTubeController:

    def search_and_play(self, query: str) -> tuple[bool, str]:
        video_id, title = self._find_video(query)

        if video_id:
            url  = f"https://www.youtube.com/watch?v={video_id}"
            name = title if title else query
        else:
            # fallback: YouTube search page
            url  = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            name = query

        ok = self._open_firefox(url)
        if not ok:
            return False, "Firefox not found. Install: sudo pacman -S firefox"

        return True, f'Playing "{name}" on YouTube in Firefox.'

    # ── yt-dlp: get video ID only (fast, no download) ─────────────────────
    def _find_video(self, query: str) -> tuple[str, str]:
        """Returns (video_id, title). Uses --get-id for reliability."""
        try:
            # Get ID
            r_id = subprocess.run(
                [sys.executable, "-m", "yt_dlp",
                 "--no-playlist", "--no-warnings", "--quiet",
                 "--get-id",
                 f"ytsearch1:{query}"],
                capture_output=True, text=True, timeout=20)
            video_id = r_id.stdout.strip().splitlines()[0].strip() \
                       if r_id.stdout.strip() else ""

            # Get title separately
            title = ""
            if video_id:
                r_title = subprocess.run(
                    [sys.executable, "-m", "yt_dlp",
                     "--no-playlist", "--no-warnings", "--quiet",
                     "--get-title",
                     f"https://www.youtube.com/watch?v={video_id}"],
                    capture_output=True, text=True, timeout=10)
                title = r_title.stdout.strip().splitlines()[0].strip() \
                        if r_title.stdout.strip() else query

            return video_id, title

        except subprocess.TimeoutExpired:
            return "", ""
        except Exception:
            return "", ""

    # ── Open URL in Firefox ───────────────────────────────────────────────
    def _open_firefox(self, url: str) -> bool:
        if not shutil.which("firefox"):
            return False

        # Check if Firefox is already running
        r = subprocess.run(["pgrep", "-x", "firefox"],
                           capture_output=True, text=True)
        already_open = r.returncode == 0

        try:
            if already_open:
                # Open in new tab of existing Firefox
                subprocess.Popen(
                    ["firefox", "--new-tab", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True)
            else:
                subprocess.Popen(
                    ["firefox", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True)
            return True
        except Exception:
            return False

    # ── Keyboard control (ydotool → xdotool fallback) ─────────────────────
    def _focus_firefox(self):
        try:
            subprocess.run(
                ["hyprctl", "dispatch", "focuswindow", "class:firefox"],
                capture_output=True, timeout=2)
        except Exception:
            pass

    def _key(self, key: str):
        if shutil.which("ydotool"):
            subprocess.run(["ydotool", "key", key],
                           capture_output=True, timeout=2)
        elif shutil.which("xdotool"):
            subprocess.run(["xdotool", "key", key],
                           capture_output=True, timeout=2)

    def pause_resume(self):
        self._focus_firefox(); time.sleep(0.3); self._key("k")

    def mute_youtube(self):
        self._focus_firefox(); time.sleep(0.3); self._key("m")

    def fullscreen(self):
        self._focus_firefox(); time.sleep(0.3); self._key("f")
PYEOF
echo "  [✓] core/youtube_ctrl.py"

# ═══════════════════════════════════════════════════════════
#  core/task_engine.py  — full dispatcher
# ═══════════════════════════════════════════════════════════
cat > "$DIR/core/task_engine.py" << 'PYEOF'
"""
Luna Task Engine v5.5 — All system commands
"""
import os, re, subprocess, sys
from pathlib import Path
from core.system_ctrl  import BrightnessCtrl, VolumeCtrl
from core.youtube_ctrl import YouTubeController


class TaskResult:
    def __init__(self, success: bool, message: str, output: str = ""):
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
        d = Path(self.mem.get("workspace_dir", str(Path.home() / "LunaWorkspace")))
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def music_dir(self) -> Path:
        d = Path(self.mem.get("download_dir", str(Path.home() / "Music")))
        d.mkdir(parents=True, exist_ok=True)
        return d

    def handle(self, text: str):
        t  = text.strip()
        tl = t.lower()

        # ── BRIGHTNESS ────────────────────────────────────────────────────
        br = self._parse_bright(tl)
        if br:
            return self._do_bright(br)

        # ── VOLUME ────────────────────────────────────────────────────────
        vol = self._parse_vol(tl)
        if vol:
            return self._do_vol(vol)

        # ── YOUTUBE keyboard shortcuts ────────────────────────────────────
        if re.search(r"\b(pause|resume)\b", tl) and \
           re.search(r"\b(video|youtube|song|music|playing)\b", tl):
            self._yt.pause_resume()
            return TaskResult(True, "YouTube paused/resumed.")

        if "mute" in tl and re.search(r"\b(video|youtube)\b", tl):
            self._yt.mute_youtube()
            return TaskResult(True, "YouTube muted.")

        # ── PLAY (YouTube search → Firefox) ──────────────────────────────
        m = re.search(
            r"^(?:play|search|find|open|put on|start|watch)"
            r"(?:\s+(?:song|music|track|video|audio))?"
            r"\s+(.+?)(?:\s+on\s+youtube|\s+on\s+yt)?\s*$",
            t, re.IGNORECASE)
        if m:
            q = m.group(1).strip()
            skip = {"volume","brightness","bright","screen","mute","unmute",
                    "up","down","set","increase","decrease"}
            if q.lower() not in skip and not any(w in q.lower() for w in skip):
                ok, msg = self._yt.search_and_play(q)
                return TaskResult(ok, msg, output=f"Query: {q}")

        # ── DOWNLOAD MP3 ──────────────────────────────────────────────────
        m = re.search(
            r"^download\s+(?:song|music|audio|track\s+)?(.+)$", t, re.IGNORECASE)
        if m:
            return self._dl_mp3(m.group(1).strip())

        # ── CREATE DIR ────────────────────────────────────────────────────
        m = re.search(
            r"create\s+(?:a\s+)?(?:dir(?:ectory)?|folder)"
            r"\s+(?:named?\s+|called?\s+)?['\"]?(\S+)['\"]?", tl)
        if m:
            return self._mkdir(m.group(1))

        # ── CREATE FILE ───────────────────────────────────────────────────
        m = re.search(
            r"create\s+(?:a\s+)?file\s+(?:named?\s+|called?\s+)?['\"]?([\w.\-]+)['\"]?", tl)
        if m:
            return self._touch(m.group(1))

        # ── SHELL ─────────────────────────────────────────────────────────
        m = re.search(r"^(?:run|execute|shell|cmd|bash|sudo)\s+(.+)$", t, re.IGNORECASE)
        if m:
            return self._shell(m.group(1))

        # ── INSTALL ───────────────────────────────────────────────────────
        m = re.search(r"^install\s+(?:package\s+)?(\S+)", tl)
        if m:
            return self._install(m.group(1))

        # ── LIST ──────────────────────────────────────────────────────────
        if re.search(r"^(?:list|ls|show)\s+(?:files?|workspace)", tl):
            return self._ls()

        # ── STATUS ────────────────────────────────────────────────────────
        if re.search(r"(?:brightness|volume|screen)\s+(?:status|level|current|percent)", tl):
            b = self._br.get()
            v = self._vol.get()
            parts = []
            if b >= 0: parts.append(f"Brightness: {b}%")
            if v >= 0: parts.append(f"Volume: {v}%")
            return TaskResult(True, " | ".join(parts) or "Could not read levels.")

        return None

    # ── Brightness ────────────────────────────────────────────────────────
    def _parse_bright(self, tl):
        kw = r"\b(bright(?:ness)?|screen|display|backlight|dim(?:mer)?)\b"
        if not re.search(kw, tl):
            return None
        if re.search(r"\b(max(?:imum)?|full|100)\b", tl):
            return {"a": "max"}
        if re.search(r"\b(min(?:imum)?|lowest|very\s*low|dark)\b", tl):
            return {"a": "min"}
        if re.search(r"\b(up|increase|brighter|higher|raise|more)\b", tl):
            m = re.search(r"(\d+)", tl); step = int(m.group(1)) if m and int(m.group(1))<=100 else 10
            return {"a": "up", "step": step}
        if re.search(r"\b(down|decrease|dim|lower|reduce|less|darker)\b", tl):
            m = re.search(r"(\d+)", tl); step = int(m.group(1)) if m and int(m.group(1))<=100 else 10
            return {"a": "down", "step": step}
        m = re.search(r"(\d{1,3})\s*%?", tl)
        if m:
            return {"a": "set", "lvl": min(int(m.group(1)), 100)}
        return None

    def _do_bright(self, cmd) -> TaskResult:
        if not self._br.available():
            return TaskResult(False,
                "brightnessctl not found.\n"
                "Fix: sudo pacman -S brightnessctl && sudo usermod -aG video $USER")
        a = cmd["a"]
        if   a == "max":  ok, msg = self._br.max_bright()
        elif a == "min":  ok, msg = self._br.min_bright()
        elif a == "up":   ok, msg = self._br.up(cmd.get("step", 10))
        elif a == "down": ok, msg = self._br.down(cmd.get("step", 10))
        elif a == "set":  ok, msg = self._br.set_pct(cmd.get("lvl", 50))
        else:             return TaskResult(False, "Unknown brightness command.")
        cur = self._br.get()
        return TaskResult(ok, msg, output=f"Current: {cur}%" if cur >= 0 else "")

    # ── Volume ────────────────────────────────────────────────────────────
    def _parse_vol(self, tl):
        # Mic
        if re.search(r"\b(mic|microphone)\b", tl):
            if "mute" in tl:   return {"a": "mic_mute"}
            if "unmute" in tl: return {"a": "mic_unmute"}
        # Mute/unmute
        if re.search(r"\bunmute\b", tl):               return {"a": "unmute"}
        if re.search(r"\bmute\b", tl) and \
           not re.search(r"\b(youtube|video)\b", tl):   return {"a": "mute"}
        # Max/min
        if re.search(r"\b(vol(?:ume)?|sound|audio)\b", tl):
            if re.search(r"\b(max(?:imum)?|full|100)\b", tl): return {"a": "max"}
            if re.search(r"\b(min(?:imum)?|zero|silent)\b", tl): return {"a": "min"}
        # Up
        if re.search(r"\b(vol(?:ume)?\s*up|turn\s*up|louder|increase\s*vol"
                     r"|raise\s*vol|sound\s*up|audio\s*up)\b", tl):
            m = re.search(r"(\d+)", tl); step = int(m.group(1)) if m and int(m.group(1))<=100 else 10
            return {"a": "up", "step": step}
        # Down
        if re.search(r"\b(vol(?:ume)?\s*down|turn\s*down|quieter|lower\s*vol"
                     r"|decrease\s*vol|sound\s*down|audio\s*down)\b", tl):
            m = re.search(r"(\d+)", tl); step = int(m.group(1)) if m and int(m.group(1))<=100 else 10
            return {"a": "down", "step": step}
        # Set exact
        m = re.search(r"(?:set\s+)?(?:vol(?:ume)?|sound|audio)\s+(?:to\s+|at\s+)?(\d{1,3})\s*%?", tl)
        if m: return {"a": "set", "lvl": min(int(m.group(1)), 150)}
        return None

    def _do_vol(self, cmd) -> TaskResult:
        if not self._vol.available():
            return TaskResult(False,
                "wpctl/pactl not found.\n"
                "Fix: sudo pacman -S pipewire pipewire-pulse wireplumber")
        a = cmd["a"]
        if   a == "mute":       ok, msg = self._vol.mute()
        elif a == "unmute":     ok, msg = self._vol.unmute()
        elif a == "max":        ok, msg = self._vol.set_pct(100)
        elif a == "min":        ok, msg = self._vol.set_pct(0)
        elif a == "up":         ok, msg = self._vol.up(cmd.get("step", 10))
        elif a == "down":       ok, msg = self._vol.down(cmd.get("step", 10))
        elif a == "set":        ok, msg = self._vol.set_pct(cmd.get("lvl", 50))
        elif a == "mic_mute":   ok, msg = self._vol.mic_mute()
        elif a == "mic_unmute": ok, msg = self._vol.mic_unmute()
        else:                   return TaskResult(False, "Unknown volume command.")
        cur = self._vol.get()
        return TaskResult(ok, msg, output=f"Current: {cur}%" if cur >= 0 else "")

    # ── Download MP3 ──────────────────────────────────────────────────────
    def _dl_mp3(self, query) -> TaskResult:
        try:
            import yt_dlp
        except ImportError:
            subprocess.run([sys.executable,"-m","pip","install","yt-dlp","-q"],
                           capture_output=True, timeout=60)
        out = str(self.music_dir / "%(title)s.%(ext)s")
        try:
            r = subprocess.run(
                [sys.executable,"-m","yt_dlp",
                 f"ytsearch1:{query}","--extract-audio",
                 "--audio-format","mp3","--audio-quality","0",
                 "-o",out,"--no-playlist",
                 "--print","after_move:filepath","--no-warnings"],
                capture_output=True, text=True, timeout=120)
            path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
            if not path or not Path(path).exists():
                files = sorted(self.music_dir.glob("*.mp3"),
                               key=os.path.getmtime, reverse=True)
                path = str(files[0]) if files else ""
            if not path:
                return TaskResult(False, f"Download failed: {(r.stderr or r.stdout)[:200]}")
            return TaskResult(True, f"Downloaded: {Path(path).name}",
                              output=f"Saved to: {path}")
        except subprocess.TimeoutExpired:
            return TaskResult(False, "Download timed out.")
        except Exception as e:
            return TaskResult(False, f"Download error: {e}")

    # ── File ops ──────────────────────────────────────────────────────────
    def _mkdir(self, name):
        try:
            t = self.workspace / name; t.mkdir(parents=True, exist_ok=True)
            return TaskResult(True, f"Created: {t}")
        except Exception as e: return TaskResult(False, str(e))

    def _touch(self, name, content=""):
        try:
            t = self.workspace / name
            t.parent.mkdir(parents=True, exist_ok=True); t.write_text(content)
            return TaskResult(True, f"Created: {t}", output=str(t))
        except Exception as e: return TaskResult(False, str(e))

    def write_code(self, filename, code, lang=""):
        ext = {"python":"py","py":"py","javascript":"js","js":"js",
               "bash":"sh","sh":"sh","html":"html","css":"css","rust":"rs"}
        if "." not in filename:
            filename += "." + ext.get(lang.lower(), "txt")
        try:
            t = self.workspace / filename
            t.parent.mkdir(parents=True, exist_ok=True); t.write_text(code)
            if filename.endswith(".sh"): os.chmod(t, 0o755)
            return TaskResult(True, f"Saved: {t}", output=str(t))
        except Exception as e: return TaskResult(False, str(e))

    def _shell(self, cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True,
                               text=True, timeout=60, cwd=str(self.workspace),
                               env={**os.environ})
            out = (r.stdout + r.stderr).strip(); ok = r.returncode == 0
            return TaskResult(ok, f"Done (exit {r.returncode}).", output=out or "(no output)")
        except subprocess.TimeoutExpired:
            return TaskResult(False, "Timed out.")
        except Exception as e: return TaskResult(False, str(e))

    def _install(self, pkg):
        for cmd in [
            [sys.executable,"-m","pip","install",pkg,"-q"],
            ["sudo","pacman","-S",pkg,"--noconfirm"],
            ["yay","-S",pkg,"--noconfirm"],
        ]:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if r.returncode == 0:
                    return TaskResult(True, f"Installed `{pkg}`.")
            except (FileNotFoundError, subprocess.TimeoutExpired): continue
        return TaskResult(False, f"Could not install `{pkg}`.")

    def _ls(self):
        files = list(self.workspace.rglob("*"))
        if not files: return TaskResult(True, "Workspace is empty.")
        lines = [f"{'📁' if f.is_dir() else '📄'} {f.relative_to(self.workspace)}"
                 for f in sorted(files)[:50]]
        return TaskResult(True, f"{len(files)} items:", output="\n".join(lines))
PYEOF
echo "  [✓] core/task_engine.py"

# ─────────────────────────────────────────────────────────────
#  Final self-test
# ─────────────────────────────────────────────────────────────
echo ""
echo "  [~] Final self-test..."

# Test brightness
$PYTHON - << 'PYTEST'
import sys
sys.path.insert(0, ".")
from core.system_ctrl import BrightnessCtrl, VolumeCtrl

br = BrightnessCtrl()
vol = VolumeCtrl()

print(f"  Brightness available: {br.available()}")
print(f"  Brightness current:   {br.get()}%")

print(f"  Volume available:     {vol.available()}")
print(f"  Volume current:       {vol.get()}%")

# Test volume up/down
ok, msg = vol.up(1)
print(f"  Volume +1%:           {ok} — {msg}")
ok, msg = vol.down(1)
print(f"  Volume -1%:           {ok} — {msg}")
PYTEST

echo ""
echo "  ╔════════════════════════════════════════════╗"
echo "  ║  ALL DONE. Commands to try in Luna:       ║"
echo "  ╠════════════════════════════════════════════╣"
echo "  ║  play believer by imagine dragons         ║"
echo "  ║  play lo fi hip hop                       ║"
echo "  ║  volume up                                ║"
echo "  ║  volume down 20                           ║"
echo "  ║  volume 60%                               ║"
echo "  ║  mute  /  unmute                          ║"
echo "  ║  brightness up                            ║"
echo "  ║  brightness down                          ║"
echo "  ║  brightness 70%                           ║"
echo "  ║  dim the screen                           ║"
echo "  ║  full brightness                          ║"
echo "  ║  volume status                            ║"
echo "  ╚════════════════════════════════════════════╝"
echo ""
echo "  Run: python main.py"
echo ""
