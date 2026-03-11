"""
Luna AI v5 — Main Window
Chat panel with code blocks, task output, system HUD
"""
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QScrollArea, QLineEdit,
        QFrame, QSizePolicy,
    )
    from PyQt6.QtCore  import Qt, QTimer, QThread, pyqtSignal
    from PyQt6.QtGui   import QFont
    _SF = Qt.FocusPolicy.StrongFocus
    _WW = Qt.TextInteractionFlag.TextSelectableByMouse
except ImportError:
    from PyQt5.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QScrollArea, QLineEdit,
        QFrame, QSizePolicy,
    )
    from PyQt5.QtCore  import Qt, QTimer, QThread, pyqtSignal
    from PyQt5.QtGui   import QFont
    _SF = Qt.StrongFocus
    _WW = Qt.TextSelectableByMouse

from ui.widgets        import StatusDot, HUDWidget, VoiceVisualizer, SystemMeter
from ui.code_block     import CodeBlockWidget
from ui.settings_panel import SettingsPanel
from core.code_parser  import parse_response


# ── Worker threads ────────────────────────────────────────────────────────────
class AIThread(QThread):
    result = pyqtSignal(str)
    failed = pyqtSignal(str)
    def __init__(self, ai, text, history):
        super().__init__()
        self.ai = ai; self.text = text; self.history = history
    def run(self):
        try:    self.result.emit(self.ai.process(self.text, self.history))
        except Exception as e: self.failed.emit(str(e))


class MicThread(QThread):
    result = pyqtSignal(str)
    failed = pyqtSignal(str)
    def run(self):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.5)
                audio = r.listen(src, timeout=8, phrase_time_limit=14)
            self.result.emit(r.recognize_google(audio))
        except ImportError: self.failed.emit("__import__")
        except Exception as e: self.failed.emit(str(e))


class TaskThread(QThread):
    result = pyqtSignal(object)
    def __init__(self, task_engine, text):
        super().__init__()
        self.te = task_engine; self.text = text
    def run(self):
        r = self.te.handle(self.text)
        self.result.emit(r)


# ── Chat bubble helpers ───────────────────────────────────────────────────────
def _msg_widget(text: str, role: str) -> QWidget:
    """Plain text message bubble."""
    w = QWidget()
    lay = QHBoxLayout(w); lay.setContentsMargins(0,2,0,2)

    bubble = QLabel(text)
    bubble.setWordWrap(True)
    bubble.setTextInteractionFlags(_WW)

    if role == "user":
        bubble.setObjectName("bubbleUser")
        lay.addStretch(); lay.addWidget(bubble)
        bubble.setMaximumWidth(520)
    elif role == "ai":
        bubble.setObjectName("bubbleAI")
        lay.addWidget(bubble); lay.addStretch()
        bubble.setMaximumWidth(600)
    elif role == "system":
        bubble.setObjectName("bubbleSystem")
        lay.addWidget(bubble); lay.addStretch()
    elif role == "task_ok":
        bubble.setObjectName("bubbleTaskOk")
        lay.addWidget(bubble); lay.addStretch()
    elif role == "task_err":
        bubble.setObjectName("bubbleTaskErr")
        lay.addWidget(bubble); lay.addStretch()

    return w


# ── Main Window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self, voice, ai, mem, task_engine):
        super().__init__()
        self.voice = voice; self.ai = ai
        self.mem   = mem;   self.te = task_engine
        self._ai_thread:   AIThread   | None = None
        self._mic_thread:  MicThread  | None = None
        self._task_thread: TaskThread | None = None

        self.setWindowTitle("LUNA AI  v5.0")
        self.setMinimumSize(1000, 720)
        self.resize(1240, 840)
        self._build()
        self._connect()
        QTimer.singleShot(0, self._start_clock)

    # ── Build ─────────────────────────────────────────────────────────────
    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        vb = QVBoxLayout(root); vb.setContentsMargins(0,0,0,0); vb.setSpacing(0)
        vb.addWidget(self._mk_header())
        body = QWidget(); body.setObjectName("bodyArea")
        hb = QHBoxLayout(body)
        hb.setContentsMargins(14,12,14,12); hb.setSpacing(14)
        hb.addWidget(self._mk_left()), hb.addWidget(self._mk_chat(), 1)
        vb.addWidget(body, 1)
        vb.addWidget(self._mk_input())

    def _mk_header(self) -> QFrame:
        bar = QFrame(); bar.setObjectName("headerBar"); bar.setFixedHeight(56)
        lay = QHBoxLayout(bar); lay.setContentsMargins(20,0,20,0); lay.setSpacing(0)

        self.status_dot  = StatusDot()
        logo = QLabel("L·U·N·A"); logo.setObjectName("logoLabel")
        sub  = QLabel("  AI v5"); sub.setObjectName("subLabel")
        self.status_text = QLabel("BOOTING"); self.status_text.setObjectName("statusText")
        lay.addWidget(self.status_dot); lay.addSpacing(10)
        lay.addWidget(logo); lay.addWidget(sub); lay.addSpacing(16)
        lay.addWidget(self.status_text); lay.addStretch()

        self.time_lbl = QLabel(); self.time_lbl.setObjectName("timeLabel")
        lay.addWidget(self.time_lbl); lay.addSpacing(16)

        self.clear_btn    = QPushButton("✕ Clear"); self.clear_btn.setObjectName("headerBtn")
        self.stop_btn     = QPushButton("⏹ Stop");  self.stop_btn.setObjectName("headerBtn")
        self.settings_btn = QPushButton("⚙ Settings"); self.settings_btn.setObjectName("headerBtn")
        for b in (self.clear_btn, self.stop_btn, self.settings_btn):
            b.setFixedHeight(32); lay.addSpacing(6); lay.addWidget(b)
        return bar

    def _mk_left(self) -> QWidget:
        w = QWidget(); w.setObjectName("leftPanel"); w.setFixedWidth(230)
        lay = QVBoxLayout(w); lay.setContentsMargins(0,0,0,0); lay.setSpacing(10)

        self.hud = HUDWidget(); self.hud.setMinimumHeight(200)
        lay.addWidget(self.hud)

        self.viz = VoiceVisualizer()
        lay.addWidget(self.viz)

        self.meters = SystemMeter()
        lay.addWidget(self.meters)

        card = QFrame(); card.setObjectName("infoCard")
        cl = QVBoxLayout(card); cl.setContentsMargins(10,8,10,8); cl.setSpacing(4)
        self.inf_provider = QLabel(); self.inf_provider.setObjectName("infoLine")
        self.inf_voice    = QLabel(); self.inf_voice.setObjectName("infoLine")
        self.inf_user     = QLabel(); self.inf_user.setObjectName("infoLine")
        self.inf_workspace= QLabel(); self.inf_workspace.setObjectName("infoLine")
        for x in (self.inf_provider, self.inf_voice, self.inf_user, self.inf_workspace):
            x.setWordWrap(True); cl.addWidget(x)
        lay.addWidget(card)
        lay.addStretch()
        self._refresh_info()
        return w

    def _mk_chat(self) -> QFrame:
        frame = QFrame(); frame.setObjectName("chatPanel")
        lay = QVBoxLayout(frame); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        hdr = QLabel("  CONVERSATION"); hdr.setObjectName("chatHeader"); hdr.setFixedHeight(36)
        lay.addWidget(hdr)
        div = QFrame(); div.setObjectName("divider"); div.setFixedHeight(1)
        lay.addWidget(div)

        # Scroll area for messages
        self._scroll = QScrollArea()
        self._scroll.setObjectName("chatScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff if hasattr(Qt,'ScrollBarPolicy') else Qt.AlwaysOff)

        self._msg_container = QWidget()
        self._msg_container.setObjectName("msgContainer")
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(14,10,14,10)
        self._msg_layout.setSpacing(6)
        self._msg_layout.addStretch()

        self._scroll.setWidget(self._msg_container)
        lay.addWidget(self._scroll, 1)
        return frame

    def _mk_input(self) -> QFrame:
        bar = QFrame(); bar.setObjectName("inputBar"); bar.setFixedHeight(68)
        lay = QHBoxLayout(bar); lay.setContentsMargins(16,12,16,12); lay.setSpacing(10)

        self.mic_btn = QPushButton("🎙"); self.mic_btn.setObjectName("micBtn")
        self.mic_btn.setFixedSize(44,44)

        self.input_field = QLineEdit(); self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText(
            "Ask Luna anything · type 'create file hello.py' · 'download song ...' · 'run ls' …")
        self.input_field.setFocusPolicy(_SF)

        self.send_btn = QPushButton("SEND  ↵"); self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedSize(110, 44)

        lay.addWidget(self.mic_btn)
        lay.addWidget(self.input_field, 1)
        lay.addWidget(self.send_btn)
        return bar

    # ── Signals ───────────────────────────────────────────────────────────
    def _connect(self):
        self.send_btn.clicked.connect(self.send)
        self.input_field.returnPressed.connect(self.send)
        self.settings_btn.clicked.connect(self._open_settings)
        self.clear_btn.clicked.connect(self._clear)
        self.stop_btn.clicked.connect(self._stop)
        self.mic_btn.clicked.connect(self._mic)

    # ── Clock ─────────────────────────────────────────────────────────────
    def _start_clock(self):
        self._tick_clock()
        t = QTimer(self); t.timeout.connect(self._tick_clock); t.start(1000)

    def _tick_clock(self):
        self.time_lbl.setText(datetime.now().strftime("%H:%M:%S"))

    # ── Status ────────────────────────────────────────────────────────────
    def set_status(self, state: str):
        self.status_text.setText(state)
        self.status_dot.set_state(state)
        self.hud.set_state(state)
        if state in ("SPEAKING","THINKING","LISTENING","WORKING"):
            self.viz.start()
        else:
            self.viz.stop()

    # ── Info refresh ──────────────────────────────────────────────────────
    def _refresh_info(self):
        p = self.mem.get("provider","?").upper()
        m = self.mem.get("model","—"); m = m.split("-")[-1] if m else "—"
        v = self.mem.get("voice","—").replace("Neural","").replace("-"," ").strip()
        u = self.mem.get_user_name() or "—"
        ws = self.mem.get("workspace_dir","—")
        import os; ws_short = "~/" + os.path.basename(ws)
        self.inf_provider.setText(f"◈ {p} · {m}")
        self.inf_voice.setText(f"◈ Voice: {v}")
        self.inf_user.setText(f"◈ User: {u}")
        self.inf_workspace.setText(f"◈ WS: {ws_short}")

    # ── Add message ───────────────────────────────────────────────────────
    def _add_msg(self, text: str, role: str):
        w = _msg_widget(text, role)
        # Insert before the stretch (last item)
        count = self._msg_layout.count()
        self._msg_layout.insertWidget(count - 1, w)
        QTimer.singleShot(30, self._scroll_bottom)

    def _add_code_block(self, code: str, lang: str, idx: int):
        w = CodeBlockWidget(code, lang, idx, self.te, self._msg_container)
        count = self._msg_layout.count()
        self._msg_layout.insertWidget(count - 1, w)
        QTimer.singleShot(30, self._scroll_bottom)

    def _add_task_output(self, output: str):
        """Monospace output box for command/task results."""
        box = QLabel(output)
        box.setObjectName("taskOutput")
        box.setWordWrap(True)
        box.setTextInteractionFlags(_WW)
        box.setFont(QFont("Consolas", 11))
        count = self._msg_layout.count()
        self._msg_layout.insertWidget(count - 1, box)
        QTimer.singleShot(30, self._scroll_bottom)

    def _scroll_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Display AI response (parse code blocks) ───────────────────────────
    def display_ai(self, text: str):
        parsed = parse_response(text)
        if parsed.explanation.strip():
            self._add_msg(parsed.explanation, "ai")
        for cb in parsed.code_blocks:
            self._add_code_block(cb.code, cb.language, cb.index)
        return parsed

    # ── Send ──────────────────────────────────────────────────────────────
    def send(self):
        text = self.input_field.text().strip()
        if not text: return
        self.input_field.clear()
        self._set_input_enabled(False)
        self._add_msg(text, "user")
        self.mem.add_to_history("user", text)

        # Check task engine first
        task_result = self.te.handle(text)
        if task_result is not None:
            self.set_status("WORKING")
            self._on_task_result(task_result)
            return

        self.set_status("THINKING")
        self._ai_thread = AIThread(self.ai, text, self.mem.get_history())
        self._ai_thread.result.connect(self._on_ai_result)
        self._ai_thread.failed.connect(self._on_ai_error)
        self._ai_thread.start()

    def _on_ai_result(self, response: str):
        self.mem.add_to_history("assistant", response)
        parsed = self.display_ai(response)
        self._set_input_enabled(True)
        self.set_status("SPEAKING")
        # Only speak the explanation
        tts = parsed.explanation if parsed.explanation else "Here's what I found."
        self.voice.speak_async(tts, on_done=lambda: self.set_status("READY"))

    def _on_ai_error(self, err: str):
        self._add_msg(f"⚠ AI error: {err}", "system")
        self._set_input_enabled(True)
        self.set_status("READY")

    def _on_task_result(self, result):
        if result.success:
            self._add_msg(f"✓ {result.message}", "task_ok")
        else:
            self._add_msg(f"✗ {result.message}", "task_err")
        if result.output:
            self._add_task_output(result.output)
        self._set_input_enabled(True)
        self.set_status("READY")
        speak = result.message.replace("`","").replace("*","")
        self.voice.speak_async(speak)

    def _set_input_enabled(self, on: bool):
        self.input_field.setEnabled(on)
        self.send_btn.setEnabled(on)
        if on: self.input_field.setFocus()

    # ── Mic ───────────────────────────────────────────────────────────────
    def _mic(self):
        self.mic_btn.setEnabled(False)
        self.set_status("LISTENING")
        self._mic_thread = MicThread()
        self._mic_thread.result.connect(self._on_mic_ok)
        self._mic_thread.failed.connect(self._on_mic_err)
        self._mic_thread.start()

    def _on_mic_ok(self, text: str):
        self.mic_btn.setEnabled(True)
        self.input_field.setText(text)
        self.set_status("READY")
        self.send()

    def _on_mic_err(self, err: str):
        self.mic_btn.setEnabled(True)
        self.set_status("READY")
        if err == "__import__":
            self._add_msg("Install SpeechRecognition: pip install SpeechRecognition pyaudio", "system")
        else:
            self._add_msg(f"Mic error: {err}", "system")

    # ── Settings ──────────────────────────────────────────────────────────
    def _open_settings(self):
        dlg = SettingsPanel(self.mem, self.voice, self)
        dlg.settings_saved.connect(self._refresh_info)
        dlg.exec()

    # ── Stop / Clear ──────────────────────────────────────────────────────
    def _stop(self):
        self.voice.stop()
        if self._ai_thread and self._ai_thread.isRunning():
            self._ai_thread.terminate()
        self._set_input_enabled(True)
        self.set_status("READY")

    def _clear(self):
        while self._msg_layout.count() > 1:
            item = self._msg_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.mem.clear_history()
        self._add_msg("Chat cleared. Ready.", "system")

    # ── Boot greeting ─────────────────────────────────────────────────────
    def greet(self):
        user = self.mem.get_user_name()
        msg = (f"Welcome back, {user}. All systems are online."
               if user else
               "Hello! I'm Luna AI v5. Open Settings ⚙ to add your API key and choose a voice.")
        self._add_msg(msg, "ai")
        self.set_status("SPEAKING")
        self.voice.speak_async(msg, on_done=lambda: self.set_status("READY"))
