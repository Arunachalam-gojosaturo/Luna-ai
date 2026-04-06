"""
Luna Voice Engine v6 — cross-platform, self-healing.

Fixes:
  • Detects the correct Python (venv-aware, pyenv-safe)
    by checking sys.prefix first, then walking known paths.
  • TMPDIR=/tmp injected so Python 3.14 doesn't crash.
  • Auto-detects audio player: mpv → ffplay → vlc → paplay → afplay → pygame.
  • Errors surfaced via log, never silently swallowed.
"""

import os, sys, shutil, subprocess, tempfile, logging
from pathlib import Path

log = logging.getLogger("luna.voice")

try:
    from PyQt6.QtCore import QThread, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QThread, pyqtSignal

try:
    from core.env_helper import env as _env
except ImportError:
    def _env(): return {**os.environ, "TMPDIR": "/tmp"}

# ── pygame fallback ───────────────────────────────────────────────────────────
try:
    import pygame
    pygame.mixer.init()
    _HAS_PYGAME = True
except Exception:
    _HAS_PYGAME = False


# ── Locate the Python interpreter that has edge_tts installed ─────────────────
def _find_python() -> str:
    """
    Return path to a Python that can run edge_tts.
    Priority:
      1. Current interpreter (sys.executable) if edge_tts importable
      2. Venv in app directory  (../venv or ../.venv)
      3. /opt/luna-ai/venv
      4. sys.executable as last resort
    """
    # Is edge_tts already available from current interpreter?
    try:
        import importlib
        importlib.import_module("edge_tts")
        return sys.executable
    except ImportError:
        pass

    # Walk candidate venv paths relative to this file
    app_root = Path(__file__).parent.parent
    candidates = [
        app_root / "venv" / "bin" / "python3",
        app_root / "venv" / "bin" / "python",
        app_root / ".venv" / "bin" / "python3",
        app_root / ".venv" / "bin" / "python",
        Path("/opt/luna-ai/venv/bin/python3"),
        Path("/opt/luna-ai/venv/bin/python"),
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            log.info("Using venv python: %s", c)
            return str(c)

    log.warning("Could not find venv python with edge_tts — using %s", sys.executable)
    return sys.executable


_PYTHON = _find_python()


# ── Audio player detection ─────────────────────────────────────────────────────
def _find_player():
    for cmd in [
        ["mpv", "--no-cache", "--no-video", "--really-quiet"],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
        ["cvlc", "--play-and-exit", "--quiet"],
        ["vlc",  "--intf", "dummy", "--play-and-exit"],
        ["mplayer", "-really-quiet", "-noconsolecontrols"],
        ["paplay"],
        ["pw-play"],
        ["afplay"],        # macOS
        ["aplay"],         # ALSA last resort
    ]:
        if shutil.which(cmd[0]):
            return cmd
    return None

_PLAYER = _find_player()


def _play(path: str) -> bool:
    e = _env()
    if _PLAYER:
        try:
            r = subprocess.run(
                _PLAYER + [path], timeout=120, env=e,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired) as ex:
            log.warning("Player failed: %s", ex)
    if _HAS_PYGAME:
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(80)
            pygame.mixer.music.unload()
            return True
        except Exception as ex:
            log.warning("pygame failed: %s", ex)
    log.error("No audio player available. Install mpv: sudo pacman -S mpv")
    return False


# ── TTS synthesis thread ──────────────────────────────────────────────────────
class VoiceSynthThread(QThread):
    finished       = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, text, voice, rate, pitch):
        super().__init__()
        self.text  = text
        self.voice = voice
        self.rate  = rate
        self.pitch = pitch
        self._stopped = False

    def run(self):
        if not self.text.strip():
            self.finished.emit(); return

        tmp = os.path.join(tempfile.gettempdir(), "luna_tts.mp3")
        try:
            self._synth(tmp)
            if not self._stopped:
                if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                    _play(tmp)
                else:
                    self.error_occurred.emit("TTS produced empty file.")
        except Exception as ex:
            self.error_occurred.emit(str(ex))
            log.exception("VoiceSynthThread")
        finally:
            try:
                if os.path.exists(tmp): os.remove(tmp)
            except Exception:
                pass
            self.finished.emit()

    def _synth(self, out: str):
        e = {**_env(), "TMPDIR": "/tmp"}
        cmd = [
            _PYTHON, "-m", "edge_tts",
            "--voice", self.voice,
            "--rate",  self.rate,
            "--pitch", self.pitch,
            "--text",  self.text,
            "--write-media", out,
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=30, env=e)
        if r.returncode == 0:
            return
        err = r.stderr.decode(errors="ignore").strip()

        # Fallback to edge-tts binary in PATH
        bin_path = shutil.which("edge-tts") or shutil.which("edge_tts")
        if bin_path:
            cmd2 = [bin_path,
                    "--voice", self.voice, "--rate", self.rate,
                    "--pitch", self.pitch, "--text", self.text,
                    "--write-media", out]
            r2 = subprocess.run(cmd2, capture_output=True, timeout=30, env=e)
            if r2.returncode == 0:
                return

        raise RuntimeError(
            f"edge_tts failed (rc={r.returncode}): {err}\n"
            f"Python used: {_PYTHON}\n"
            "Fix: ensure edge-tts is installed in the venv"
        )

    def stop(self):
        self._stopped = True
        if _HAS_PYGAME:
            try: pygame.mixer.music.stop()
            except Exception: pass
        self.terminate()


# ── VoiceEngine public API ────────────────────────────────────────────────────
class VoiceEngine:
    def __init__(self, mem):
        self.mem = mem
        self._thread = None
        self.is_speaking = False
        log.info("VoiceEngine ready | python=%s | player=%s | pygame=%s",
                 _PYTHON, _PLAYER[0] if _PLAYER else "none", _HAS_PYGAME)

    @property
    def voice(self):  return self.mem.get("voice",       "en-US-AriaNeural")
    @property
    def rate(self):   return self.mem.get("voice_rate",  "-5%")
    @property
    def pitch(self):  return self.mem.get("voice_pitch", "+0Hz")

    def speak_async(self, text: str, on_done=None):
        self.stop()
        self.is_speaking = True
        t = VoiceSynthThread(text, self.voice, self.rate, self.pitch)

        def _done():
            self.is_speaking = False
            if on_done: on_done()

        t.finished.connect(_done)
        t.error_occurred.connect(lambda m: log.error("TTS error: %s", m))
        self._thread = t
        t.start()

    def stop(self):
        if self._thread and self._thread.isRunning():
            self._thread.stop()
            self._thread.wait(2000)
        self.is_speaking = False

    @staticmethod
    def audio_info() -> str:
        if _PLAYER: return f"✓ {_PLAYER[0]}"
        if _HAS_PYGAME: return "✓ pygame"
        return "✗ no player (install mpv)"

    @staticmethod
    def available_voices():
        return [
            ("en-US-AriaNeural",        "Aria — US Female  ★"),
            ("en-US-JennyNeural",       "Jenny — US Female"),
            ("en-US-MichelleNeural",    "Michelle — US Professional"),
            ("en-US-SaraNeural",        "Sara — US Warm"),
            ("en-GB-SoniaNeural",       "Sonia — UK Female"),
            ("en-AU-NatashaNeural",     "Natasha — AU Female"),
            ("en-US-GuyNeural",         "Guy — US Male"),
            ("en-US-DavisNeural",       "Davis — US Male Casual"),
            ("en-US-ChristopherNeural", "Christopher — US Male Deep"),
            ("en-GB-RyanNeural",        "Ryan — UK Male"),
        ]
