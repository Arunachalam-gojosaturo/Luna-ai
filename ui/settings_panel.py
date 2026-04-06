try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QComboBox, QSlider, QTabWidget, QWidget, QFrame,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    _H    = Qt.Orientation.Horizontal
    _PASS = QLineEdit.EchoMode.Password
    _NORM = QLineEdit.EchoMode.Normal
    _TICKS = QSlider.TickPosition.TicksBelow
except ImportError:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QComboBox, QSlider, QTabWidget, QWidget, QFrame,
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    _H    = Qt.Horizontal
    _PASS = QLineEdit.Password
    _NORM = QLineEdit.Normal
    _TICKS = QSlider.TicksBelow

from pathlib import Path
from core.ai_engine    import AIEngine
from core.voice_engine import VoiceEngine


class SettingsPanel(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, mem, voice_engine, parent=None):
        super().__init__(parent)
        self.mem   = mem
        self.voice = voice_engine
        self.setWindowTitle("Luna — Settings")
        self.setMinimumSize(560, 520)
        self.setModal(True)
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Title
        tb = QFrame(); tb.setObjectName("settingsTitleBar"); tb.setFixedHeight(52)
        tl = QHBoxLayout(tb); tl.setContentsMargins(22,0,22,0)
        t = QLabel("⚙  SETTINGS"); t.setObjectName("settingsTitle")
        tl.addWidget(t); tl.addStretch()
        root.addWidget(tb)

        self.tabs = QTabWidget(); self.tabs.setObjectName("settingsTabs")
        self.tabs.addTab(self._ai_tab(),   "🤖  AI Model")
        self.tabs.addTab(self._voice_tab(),"🔊  Voice")
        self.tabs.addTab(self._sys_tab(),  "⚙  System")
        self.tabs.addTab(self._about_tab(),"ℹ  About")
        root.addWidget(self.tabs, 1)

        bb = QFrame(); bb.setObjectName("settingsBtnBar")
        bl = QHBoxLayout(bb); bl.setContentsMargins(20,10,20,10)
        self.cancel_btn = QPushButton("Cancel"); self.cancel_btn.setObjectName("cancelBtn")
        self.save_btn   = QPushButton("Save && Apply"); self.save_btn.setObjectName("saveBtn")
        bl.addStretch(); bl.addWidget(self.cancel_btn); bl.addSpacing(10); bl.addWidget(self.save_btn)
        root.addWidget(bb)

        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save)

    # ── AI tab ────────────────────────────────────────────────────────────
    def _ai_tab(self):
        tab = QWidget(); lay = QVBoxLayout(tab)
        lay.setContentsMargins(22,16,22,16); lay.setSpacing(12)

        lay.addWidget(self._sec("AI PROVIDER"))
        self.provider_box = QComboBox(); self.provider_box.setObjectName("settingsCombo")
        self.provider_box.addItems(["Gemini  (Google)","Groq  (Free + Fast)","Ollama  (Local / Offline)"])
        lay.addWidget(self.provider_box)

        lay.addWidget(self._sec("MODEL"))
        self.model_box = QComboBox(); self.model_box.setObjectName("settingsCombo")
        lay.addWidget(self.model_box)

        self.key_sec = self._sec("API KEY")
        lay.addWidget(self.key_sec)
        row = QHBoxLayout()
        self.key_input = QLineEdit(); self.key_input.setObjectName("settingsInput")
        self.key_input.setEchoMode(_PASS)
        self.eye = QPushButton("👁"); self.eye.setObjectName("iconBtn")
        self.eye.setFixedSize(34,34); self.eye.setCheckable(True)
        self.eye.toggled.connect(lambda on: self.key_input.setEchoMode(_NORM if on else _PASS))
        row.addWidget(self.key_input); row.addWidget(self.eye)
        lay.addLayout(row)
        self.key_link = QLabel(); self.key_link.setObjectName("linkLabel")
        self.key_link.setOpenExternalLinks(True)
        lay.addWidget(self.key_link)

        self.ollama_sec = self._sec("LOCAL MODEL NAME")
        self.ollama_in  = QLineEdit(); self.ollama_in.setObjectName("settingsInput")
        self.ollama_in.setPlaceholderText("llama3, mistral, phi3, codellama …")
        lay.addWidget(self.ollama_sec); lay.addWidget(self.ollama_in)
        lay.addStretch()
        self.provider_box.currentIndexChanged.connect(self._on_provider)
        return tab

    # ── Voice tab ─────────────────────────────────────────────────────────
    def _voice_tab(self):
        tab = QWidget(); lay = QVBoxLayout(tab)
        lay.setContentsMargins(22,16,22,16); lay.setSpacing(12)

        lay.addWidget(self._sec("VOICE"))
        self.voice_box = QComboBox(); self.voice_box.setObjectName("settingsCombo")
        for vid, vlbl in VoiceEngine.available_voices():
            self.voice_box.addItem(vlbl, vid)
        lay.addWidget(self.voice_box)

        lay.addWidget(self._sec("SPEECH RATE  (slower ←→ faster)"))
        self.rate_sld = QSlider(_H); self.rate_sld.setObjectName("settingsSlider")
        self.rate_sld.setRange(-30,30); self.rate_sld.setValue(-5)
        self.rate_sld.setTickPosition(_TICKS); self.rate_sld.setTickInterval(10)
        self.rate_val = QLabel("-5%"); self.rate_val.setObjectName("valueLabel"); self.rate_val.setFixedWidth(46)
        self.rate_sld.valueChanged.connect(lambda v: self.rate_val.setText(f"{v:+d}%"))
        rr = QHBoxLayout(); rr.addWidget(self.rate_sld,1); rr.addWidget(self.rate_val)
        lay.addLayout(rr)

        lay.addWidget(self._sec("PITCH  (lower ←→ higher)"))
        self.pitch_sld = QSlider(_H); self.pitch_sld.setObjectName("settingsSlider")
        self.pitch_sld.setRange(-20,20); self.pitch_sld.setValue(0)
        self.pitch_val = QLabel("+0Hz"); self.pitch_val.setObjectName("valueLabel"); self.pitch_val.setFixedWidth(46)
        self.pitch_sld.valueChanged.connect(lambda v: self.pitch_val.setText(f"{v:+d}Hz"))
        pr = QHBoxLayout(); pr.addWidget(self.pitch_sld,1); pr.addWidget(self.pitch_val)
        lay.addLayout(pr)

        self.test_btn = QPushButton("▶  Test Voice"); self.test_btn.setObjectName("testBtn")
        self.test_btn.clicked.connect(self._test_voice)
        lay.addWidget(self.test_btn)
        lay.addStretch()
        return tab

    # ── System tab ────────────────────────────────────────────────────────
    def _sys_tab(self):
        tab = QWidget(); lay = QVBoxLayout(tab)
        lay.setContentsMargins(22,16,22,16); lay.setSpacing(12)

        lay.addWidget(self._sec("WORKSPACE DIRECTORY  (code & files saved here)"))
        self.ws_input = QLineEdit(); self.ws_input.setObjectName("settingsInput")
        lay.addWidget(self.ws_input)

        lay.addWidget(self._sec("MUSIC DOWNLOAD DIRECTORY"))
        self.dl_input = QLineEdit(); self.dl_input.setObjectName("settingsInput")
        lay.addWidget(self.dl_input)

        info = QLabel(
            "<span style='color:rgba(0,180,255,0.55);font-size:11px;font-family:Consolas;'>"
            "Luna has full system access: create files, run commands,<br>"
            "download music via yt-dlp, install packages, and more.<br><br>"
            "Commands to try:<br>"
            "  • create dir my_project<br>"
            "  • create file hello.py<br>"
            "  • download song bohemian rhapsody<br>"
            "  • run ls -la<br>"
            "  • install numpy"
            "</span>")
        info.setWordWrap(True)
        lay.addWidget(info)
        lay.addStretch()
        return tab

    # ── About tab ─────────────────────────────────────────────────────────
    def _about_tab(self):
        tab = QWidget(); lay = QVBoxLayout(tab)
        lay.setContentsMargins(22,20,22,20)
        lbl = QLabel("""
<h2 style='color:#00c8ff;font-family:Consolas;'>L·U·N·A  AI  v5.0</h2>
<p style='color:#8aa0b8;line-height:1.9;'>
Language Understanding Neural Agent<br>
Built with PyQt6 · edge-tts · Gemini / Groq / Ollama
</p>
<p style='color:#7a8fa8;line-height:1.9;font-size:12px;'>
<b style='color:#aac8e0;'>Voice:      </b> Microsoft Edge TTS (edge-tts)<br>
<b style='color:#aac8e0;'>Downloads:</b>  yt-dlp (YouTube audio)<br>
<b style='color:#aac8e0;'>File ops: </b>  Full workspace access<br>
<b style='color:#aac8e0;'>Commands:</b>  Shell execution engine<br><br>
<b style='color:#aac8e0;'>Free API keys:</b><br>
• Gemini: <a href='https://aistudio.google.com/app/apikey' style='color:#00c8ff;'>aistudio.google.com</a><br>
• Groq: &nbsp;&nbsp;<a href='https://console.groq.com/keys' style='color:#00c8ff;'>console.groq.com</a>
</p>""")
        lbl.setOpenExternalLinks(True); lbl.setWordWrap(True)
        lay.addWidget(lbl); lay.addStretch()
        return tab

    # ── Load / Save ───────────────────────────────────────────────────────
    def _load(self):
        pmap = {"gemini":0,"groq":1,"ollama":2}
        idx = pmap.get(self.mem.get("provider","gemini"),0)
        self.provider_box.setCurrentIndex(idx)
        self._on_provider(idx)

        cur = self.mem.get("model","")
        for i in range(self.model_box.count()):
            if self.model_box.itemData(i) == cur:
                self.model_box.setCurrentIndex(i); break

        if idx == 0: self.key_input.setText(self.mem.get("api_key",""))
        elif idx == 1: self.key_input.setText(self.mem.get("groq_api_key",""))
        self.ollama_in.setText(self.mem.get("ollama_model","llama3"))

        cur_v = self.mem.get("voice","en-US-AriaNeural")
        for i in range(self.voice_box.count()):
            if self.voice_box.itemData(i) == cur_v:
                self.voice_box.setCurrentIndex(i); break

        try: self.rate_sld.setValue(int(self.mem.get("voice_rate","-5%").replace("%","")))
        except: pass
        try: self.pitch_sld.setValue(int(self.mem.get("voice_pitch","+0Hz").replace("Hz","")))
        except: pass

        self.ws_input.setText(self.mem.get("workspace_dir",str(Path.home()/"LunaWorkspace")))
        self.dl_input.setText(self.mem.get("download_dir",str(Path.home()/"Music")))

    def _on_provider(self, idx):
        self.model_box.clear()
        self.key_input.setEnabled(True)
        if idx == 0:
            for mid,lbl in AIEngine.gemini_models(): self.model_box.addItem(lbl,mid)
            self.key_sec.setText("GEMINI API KEY")
            self.key_input.setPlaceholderText("AIzaSy…")
            self.key_link.setText("<a href='https://aistudio.google.com/app/apikey' style='color:#00c8ff;'>Get free key → aistudio.google.com</a>")
            self.ollama_sec.setVisible(False); self.ollama_in.setVisible(False)
        elif idx == 1:
            for mid,lbl in AIEngine.groq_models(): self.model_box.addItem(lbl,mid)
            self.key_sec.setText("GROQ API KEY")
            self.key_input.setPlaceholderText("gsk_…")
            self.key_input.setText(self.mem.get("groq_api_key",""))
            self.key_link.setText("<a href='https://console.groq.com/keys' style='color:#00c8ff;'>Get free key → console.groq.com</a>")
            self.ollama_sec.setVisible(False); self.ollama_in.setVisible(False)
        elif idx == 2:
            self.model_box.addItem("(see local model field below)","ollama-local")
            self.key_sec.setText("API KEY  (not needed)")
            self.key_input.setPlaceholderText("not required")
            self.key_input.setEnabled(False)
            self.key_link.setText("<a href='https://ollama.com' style='color:#00c8ff;'>Install Ollama → ollama.com</a>")
            self.ollama_sec.setVisible(True); self.ollama_in.setVisible(True)

    def _save(self):
        pmap = {0:"gemini",1:"groq",2:"ollama"}
        idx = self.provider_box.currentIndex()
        s = {
            "provider":     pmap.get(idx,"gemini"),
            "model":        self.model_box.currentData() or "",
            "ollama_model": self.ollama_in.text().strip() or "llama3",
            "voice":        self.voice_box.currentData(),
            "voice_rate":   f"{self.rate_sld.value():+d}%",
            "voice_pitch":  f"{self.pitch_sld.value():+d}Hz",
            "workspace_dir": self.ws_input.text().strip(),
            "download_dir":  self.dl_input.text().strip(),
        }
        if idx == 0: s["api_key"] = self.key_input.text().strip()
        elif idx == 1: s["groq_api_key"] = self.key_input.text().strip()
        self.mem.update_settings(s)
        self.settings_saved.emit()
        self.accept()

    @staticmethod
    def _sec(text):
        l = QLabel(text); l.setObjectName("settingsSectionLabel"); return l

    def _test_voice(self):
        self.test_btn.setEnabled(False); self.test_btn.setText("▶  Speaking…")
        prev = {k: self.mem.get(k) for k in ("voice","voice_rate","voice_pitch")}
        self.mem.data["voice"]       = self.voice_box.currentData()
        self.mem.data["voice_rate"]  = f"{self.rate_sld.value():+d}%"
        self.mem.data["voice_pitch"] = f"{self.pitch_sld.value():+d}Hz"
        def restore():
            for k,v in prev.items(): self.mem.data[k] = v
            self.test_btn.setEnabled(True); self.test_btn.setText("▶  Test Voice")
        self.voice.speak_async("Hello! This is your Luna AI voice preview. Sounds great!", on_done=restore)
