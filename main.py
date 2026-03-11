#!/usr/bin/env python3
"""
L.U.N.A. AI  v5.0
Language Understanding Neural Agent

New in v5:
  • Hacker boot animation (matrix rain + sequential log)
  • Code blocks with copy/paste + save to file
  • AI speaks explanation only — not code
  • System task engine: create files/dirs, run commands, download music
  • Syntax-highlighted inline code display
  • Real-time CPU/RAM/Disk gauges
  • Stop button, mic input, responsive chat bubbles
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ── Qt import ────────────────────────────────────────────────────────────────
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore    import QTimer
    _QT6 = True
except ImportError:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore    import QTimer
    try:
        from PyQt5.QtCore import Qt
        _QT5_ATTRS = True
    except ImportError:
        _QT5_ATTRS = False
    _QT6 = False

from core.memory       import MemoryManager
from core.voice_engine import VoiceEngine
from core.ai_engine    import AIEngine
from core.task_engine  import TaskEngine
from ui.boot_screen    import BootScreen
from ui.main_window    import MainWindow


class LunaApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("LUNA AI")
        self.app.setApplicationVersion("5.0")

        if not _QT6:
            try:
                from PyQt5.QtCore import Qt
                self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
                self.app.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)
            except AttributeError:
                pass

        # ── Core modules ──
        self.mem   = MemoryManager()
        self.voice = VoiceEngine(self.mem)
        self.ai    = AIEngine(self.mem)
        self.te    = TaskEngine(self.mem)

        self._load_theme()

        # ── Boot screen ──
        self.boot = BootScreen()
        self.boot.boot_complete.connect(self._on_boot_done)
        self.boot.show()

    def _load_theme(self):
        qss = Path(__file__).parent / "ui" / "styles" / "theme.qss"
        if qss.exists():
            self.app.setStyleSheet(qss.read_text(encoding="utf-8"))

    def _on_boot_done(self):
        self.boot.hide()
        self.boot.deleteLater()

        self.win = MainWindow(self.voice, self.ai, self.mem, self.te)
        self.win.show()
        QTimer.singleShot(300, self.win.greet)

    def run(self) -> int:
        if _QT6:
            return self.app.exec()
        else:
            return self.app.exec_()


if __name__ == "__main__":
    sys.exit(LunaApp().run())
