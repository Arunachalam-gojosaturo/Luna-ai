import os, json, queue, threading
from pathlib import Path
try:
    from PyQt6.QtCore import QThread, pyqtSignal, QObject
except ImportError:
    from PyQt5.QtCore import QThread, pyqtSignal, QObject

WAKE_WORDS = {"luna", "lunar", "lena", "lune"}
VOSK_MODEL = str(Path.home() / ".luna_ai" / "vosk-model-small-en-us")

class WakeWordEngine(QThread):
    wake_detected  = pyqtSignal()
    command_heard  = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running  = True
        self._awake    = False
        self._paused   = False
        self._lock     = threading.Lock()

    def pause(self): self._paused = True
    def resume(self): self._paused = False
    def stop_engine(self): self._running = False

    def run(self):
        try:
            import vosk, pyaudio
            self._run_vosk(vosk, pyaudio)
        except ImportError:
            self._run_google_fallback()

    def _run_vosk(self, vosk, pyaudio):
        if not Path(VOSK_MODEL).exists():
            self._run_google_fallback()
            return
        vosk.SetLogLevel(-1)
        model = vosk.Model(VOSK_MODEL)
        rec   = vosk.KaldiRecognizer(model, 16000)
        pa   = pyaudio.PyAudio()
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
        stream.start_stream()
        self.status_changed.emit("idle")

        while self._running:
            try: data = stream.read(4096, exception_on_overflow=False)
            except Exception: continue
            if self._paused: continue

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result()).get("text", "").lower().strip()
                if not result: continue
                if not self._awake:
                    if any(w in result.split() for w in WAKE_WORDS):
                        self._awake = True
                        self.wake_detected.emit()
                        self.status_changed.emit("awake")
                        rec = vosk.KaldiRecognizer(model, 16000)
                else:
                    cmd = result
                    for w in WAKE_WORDS: cmd = cmd.replace(w, "").strip()
                    if cmd:
                        self.command_heard.emit(cmd)
                        self._awake = False
                        self.status_changed.emit("idle")
                        rec = vosk.KaldiRecognizer(model, 16000)
        stream.stop_stream(); stream.close(); pa.terminate()

    def _run_google_fallback(self):
        try: import speech_recognition as sr
        except ImportError: return
        recognizer = sr.Recognizer()
        self.status_changed.emit("idle")
        while self._running:
            if self._paused: import time; time.sleep(0.2); continue
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    if not self._awake:
                        try:
                            audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                            text = recognizer.recognize_google(audio).lower()
                            if any(w in text.split() for w in WAKE_WORDS):
                                self._awake = True
                                self.wake_detected.emit()
                                self.status_changed.emit("awake")
                        except (sr.WaitTimeoutError, sr.UnknownValueError): pass
                    else:
                        try:
                            audio = recognizer.listen(source, timeout=5, phrase_time_limit=12)
                            text = recognizer.recognize_google(audio).lower()
                            for w in WAKE_WORDS: text = text.replace(w, "").strip()
                            if text:
                                self.command_heard.emit(text)
                                self._awake = False
                                self.status_changed.emit("idle")
                        except (sr.WaitTimeoutError, sr.UnknownValueError):
                            self._awake = False
                            self.status_changed.emit("idle")
            except Exception: import time; time.sleep(0.5)
