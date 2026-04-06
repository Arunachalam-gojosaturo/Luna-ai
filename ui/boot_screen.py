"""
Luna AI v6 — Boot Screen
Matrix rain canvas + sequential log + progress bar.
Pure QTimer-based, no threads needed.
"""
import random, math

try:
    from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QProgressBar, QWidget
    from PyQt6.QtCore    import Qt, QTimer, pyqtSignal, QRect
    from PyQt6.QtGui     import QPainter, QColor, QFont, QPen
    _Q6 = True
except ImportError:
    from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QProgressBar, QWidget
    from PyQt5.QtCore    import Qt, QTimer, pyqtSignal, QRect
    from PyQt5.QtGui     import QPainter, QColor, QFont, QPen
    _Q6 = False


# ── Matrix Rain canvas ────────────────────────────────────────────────────────
_CHARS = "01アイウエオカキクケコサシスセソタチツテトABCDEFGHIJKLMNOPQRSTUVWXYZ#@%&"

class MatrixRain(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground if _Q6
                         else Qt.WA_TranslucentBackground)
        self._cols   = 0
        self._drops  = []
        self._chars  = []
        self._speeds = []
        self._timer  = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(55)
        self._frame  = 0
        self._fade   = 1.0  # 1.0 = fully visible, fades out during done

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._reset()

    def _reset(self):
        w = self.width()
        col_w = 14
        self._cols  = max(1, w // col_w)
        self._drops = [random.randint(-60, 0) for _ in range(self._cols)]
        self._chars = [
            [random.choice(_CHARS) for _ in range(60)]
            for _ in range(self._cols)
        ]
        self._speeds = [random.uniform(0.4, 1.0) for _ in range(self._cols)]

    def _tick(self):
        self._frame += 1
        for i in range(self._cols):
            self._drops[i] += self._speeds[i]
            h = self.height() // 14
            if self._drops[i] > h + 10:
                self._drops[i] = random.randint(-20, 0)
                self._speeds[i] = random.uniform(0.4, 1.0)
            # Occasionally mutate a char
            if random.random() < 0.06:
                row = random.randint(0, 59)
                self._chars[i][row] = random.choice(_CHARS)
        self.update()

    def paintEvent(self, e):
        if not self._cols:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing if _Q6
                       else QPainter.Antialiasing)

        col_w = self.width() / max(1, self._cols)
        row_h = 14
        font  = QFont("JetBrains Mono", 9)
        font.setBold(False)
        p.setFont(font)

        for ci in range(self._cols):
            drop = int(self._drops[ci])
            for ri in range(max(0, drop - 30), drop + 1):
                if ri < 0: continue
                dist = drop - ri
                if dist == 0:
                    alpha = int(255 * self._fade)
                    color = QColor(220, 255, 255, alpha)
                elif dist < 5:
                    alpha = int((1 - dist / 5) * 180 * self._fade)
                    color = QColor(0, 200, 255, alpha)
                elif dist < 20:
                    alpha = int((1 - dist / 20) * 90 * self._fade)
                    color = QColor(0, 140, 180, alpha)
                else:
                    continue

                char_idx = ri % 60
                ch = self._chars[ci][char_idx]
                x  = int(ci * col_w)
                y  = ri * row_h
                p.setPen(QPen(color))
                p.drawText(x, y, int(col_w), row_h,
                           (Qt.AlignmentFlag.AlignCenter if _Q6
                            else Qt.AlignCenter), ch)
        p.end()

    def fade_out(self):
        """Start fade-out animation."""
        steps = [0]
        def _step():
            self._fade = max(0.0, self._fade - 0.07)
            if self._fade <= 0:
                self._timer.stop()
        t = QTimer(self)
        t.timeout.connect(_step)
        t.start(40)


# ── Boot log lines ────────────────────────────────────────────────────────────
_LOG_LINES = [
    ("INIT",    "Loading neural core modules..."),
    ("INIT",    "Mounting memory subsystem..."),
    ("INIT",    "Voice synthesis engine: edge-tts"),
    ("INIT",    "Audio player detection..."),
    ("INIT",    "PyQt6 display layer ready"),
    ("INIT",    "AI engine initializing..."),
    ("INIT",    "Task engine armed (brightness/volume/YouTube)"),
    ("INIT",    "Web search module loaded"),
    ("INIT",    "Wake word engine standby"),
    ("INIT",    "System control interface ready"),
    ("INIT",    "History & memory manager online"),
    ("OK",      "All modules nominal"),
    ("LAUNCH",  "L.U.N.A. v6 — ONLINE"),
]


# ── Boot Screen window ─────────────────────────────────────────────────────────
class BootScreen(QFrame):
    boot_complete = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("bootFrame")
        self.setWindowFlags(
            (Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window) if _Q6
            else (Qt.FramelessWindowHint | Qt.Window))
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground if _Q6
            else Qt.WA_TranslucentBackground, False)
        self.resize(960, 560)
        self._center()
        self._build()

        self._log_idx = 0
        self._progress = 0
        self._step_timer = QTimer(self)
        self._step_timer.timeout.connect(self._next_step)
        self._step_timer.start(160)

    def _center(self):
        try:
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
        except Exception:
            try:
                from PyQt5.QtWidgets import QApplication
                screen = QApplication.primaryScreen().geometry()
            except Exception:
                return
        self.move((screen.width() - self.width()) // 2,
                  (screen.height() - self.height()) // 2)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(0)

        # Matrix rain background
        self._matrix = MatrixRain(self)
        self._matrix.setGeometry(0, 0, 960, 560)
        self._matrix.lower()

        # Title
        title = QLabel("L·U·N·A")
        title.setObjectName("bootTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter if _Q6 else Qt.AlignCenter)

        sub = QLabel("Language Understanding Neural Agent  ·  v6.0")
        sub.setObjectName("bootSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter if _Q6 else Qt.AlignCenter)

        lay.addStretch(2)
        lay.addWidget(title)
        lay.addSpacing(6)
        lay.addWidget(sub)
        lay.addStretch(1)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setObjectName("bootBar")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(4)
        self._bar.setTextVisible(False)
        lay.addWidget(self._bar)
        lay.addSpacing(12)

        # Log output
        self._log_lbl = QLabel("Initializing...")
        self._log_lbl.setObjectName("bootLog")
        self._log_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft if _Q6 else Qt.AlignLeft)
        self._log_lbl.setFixedHeight(22)
        lay.addWidget(self._log_lbl)
        lay.addStretch(1)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._matrix.setGeometry(0, 0, self.width(), self.height())

    def _next_step(self):
        total = len(_LOG_LINES)
        if self._log_idx >= total:
            self._step_timer.stop()
            self._matrix.fade_out()
            QTimer.singleShot(500, self.boot_complete.emit)
            return

        tag, msg = _LOG_LINES[self._log_idx]
        colors = {"OK": "#34d399", "LAUNCH": "#00c8ff", "INIT": "#64748b"}
        color  = colors.get(tag, "#64748b")
        self._log_lbl.setText(
            f'<span style="color:{color};letter-spacing:2px;">[{tag}]</span>'
            f'<span style="color:#94a3b8;"> {msg}</span>'
        )
        self._log_lbl.setTextFormat(
            Qt.TextFormat.RichText if _Q6 else Qt.RichText)

        self._progress = int((self._log_idx + 1) / total * 100)
        self._bar.setValue(self._progress)
        self._log_idx += 1
