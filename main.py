#!/usr/bin/env python3
"""
L.U.N.A. AI  v6.0
Language Understanding Neural Agent

New in v6:
  • Rebuilt dark glass UI with new color system
  • Matrix rain boot animation (QTimer-based, no threads)
  • Self-locating voice engine — works with any venv/pyenv setup
  • TMPDIR=/tmp fix for Python 3.14 pip/subprocess issues
  • Auto audio-player detection: mpv → ffplay → vlc → pygame
  • Avatar bubbles in chat
  • Animated HUD arc-reactor, voice visualizer, system meters
  • Universal install.sh (no rsync, uses cp/cpio)
"""
import sys, logging
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-18s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore    import QTimer
    _Q6 = True
except ImportError:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore    import QTimer
    try:
        from PyQt5.QtCore import Qt
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)
    except Exception:
        pass
    _Q6 = False

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
        self.app.setApplicationVersion("6.0")

        self._load_theme()

        self.mem   = MemoryManager()
        self.voice = VoiceEngine(self.mem)
        self.ai    = AIEngine(self.mem)
        self.te    = TaskEngine(self.mem)

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
        return self.app.exec() if _Q6 else self.app.exec_()


if __name__ == "__main__":
    sys.exit(LunaApp().run())
