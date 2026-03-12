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
