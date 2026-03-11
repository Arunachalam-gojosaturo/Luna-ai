import subprocess, os, sys, tempfile

try:
    from PyQt6.QtCore import QThread, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QThread, pyqtSignal


class VoiceSynthThread(QThread):
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, text, voice, rate, pitch):
        super().__init__()
        self.text = text; self.voice = voice
        self.rate = rate; self.pitch = pitch
        self._stopped = False

    def run(self):
        if not self.text.strip():
            self.finished.emit(); return
        tmp = os.path.join(tempfile.gettempdir(), "luna_tts.mp3")
        try:
            r = subprocess.run(
                [sys.executable, "-m", "edge_tts",
                 "--voice", self.voice, "--rate", self.rate,
                 "--pitch", self.pitch, "--text", self.text,
                 "--write-media", tmp],
                capture_output=True, timeout=30)
            if r.returncode != 0 or not os.path.exists(tmp):
                self.error_occurred.emit(r.stderr.decode(errors="ignore")); return
            if not self._stopped:
                for cmd in [
                    ["mpv","--no-cache","--no-video","--really-quiet", tmp],
                    ["ffplay","-nodisp","-autoexit","-loglevel","quiet", tmp],
                    ["cvlc","--play-and-exit","--quiet", tmp],
                ]:
                    try:
                        subprocess.run(cmd, timeout=120, capture_output=True); break
                    except (FileNotFoundError, subprocess.TimeoutExpired): continue
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            try:
                if os.path.exists(tmp): os.remove(tmp)
            except: pass
            self.finished.emit()

    def stop(self):
        self._stopped = True; self.terminate()


class VoiceEngine:
    def __init__(self, mem):
        self.mem = mem
        self._thread = None
        self.is_speaking = False

    @property
    def voice(self):  return self.mem.get("voice",       "en-US-AriaNeural")
    @property
    def rate(self):   return self.mem.get("voice_rate",  "-5%")
    @property
    def pitch(self):  return self.mem.get("voice_pitch", "+0Hz")

    def speak_async(self, text: str, on_done=None):
        self.stop()
        self.is_speaking = True
        self._thread = VoiceSynthThread(text, self.voice, self.rate, self.pitch)
        def _done():
            self.is_speaking = False
            if on_done: on_done()
        self._thread.finished.connect(_done)
        self._thread.start()

    def stop(self):
        if self._thread and self._thread.isRunning():
            self._thread.stop(); self._thread.wait(2000)
        self.is_speaking = False

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
