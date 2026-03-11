"""
Luna AI — Hacker Boot Animation Screen
Matrix rain + sequential boot messages + progress bar
"""
import random, math

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
    from PyQt6.QtCore    import Qt, QTimer, QRect, pyqtSignal
    from PyQt6.QtGui     import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
    _AA   = QPainter.RenderHint.Antialiasing
    _TEXT = QPainter.RenderHint.TextAntialiasing
    _NO_PEN   = Qt.PenStyle.NoPen
    _ALIGN_L  = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    _ALIGN_C  = Qt.AlignmentFlag.AlignCenter
    _ALIGN_R  = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    _WS_STYLED = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
except ImportError:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
    from PyQt5.QtCore    import Qt, QTimer, QRect, pyqtSignal
    from PyQt5.QtGui     import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
    _AA   = QPainter.Antialiasing
    _TEXT = QPainter.TextAntialiasing
    _NO_PEN   = Qt.NoPen
    _ALIGN_L  = Qt.AlignLeft | Qt.AlignVCenter
    _ALIGN_C  = Qt.AlignCenter
    _ALIGN_R  = Qt.AlignRight | Qt.AlignVCenter
    _WS_STYLED = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint


_MATRIX_CHARS = (
    "01アイウエオカキクケコサシスセソタチツテトナニヌネノ"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZΨΩΞΛΔΘΦΣΠabcdefgh"
    "ijklmnopqrstuvwxyz0123456789!@#$%^&*<>?/|\\~±×÷"
)

_BOOT_LINES = [
    ("[BIOS]  POST check.......................... OK",       0.00),
    ("[BIOS]  RAM detected: 32 GB DDR5............. OK",     0.06),
    ("[KERN]  Loading neural kernel v5.0.......... OK",      0.12),
    ("[INIT]  Mounting encrypted filesystem........ OK",     0.18),
    ("[NET]   Establishing secure channel.......... OK",     0.26),
    ("[AI]    Loading language model weights....... OK",     0.34),
    ("[AI]    Initializing voice synthesis......... OK",     0.42),
    ("[AI]    Calibrating voice recognition........ OK",     0.50),
    ("[SYS]   Connecting to AI backend............ OK",      0.58),
    ("[UI]    Rendering holographic interface...... OK",     0.66),
    ("[MEM]   Loading user profile & memory........ OK",     0.74),
    ("[TASK]  Initializing system task engine...... OK",     0.82),
    ("[PERM]  Granting elevated permissions......... OK",    0.90),
    ("[LUNA]  All systems online. Ready............. OK",    0.97),
]


class MatrixColumn:
    def __init__(self, x: int, h: int, font_size: int):
        self.x = x
        self.font_size = font_size
        self.speed = random.uniform(1.0, 2.8)
        self.length = random.randint(8, 22)
        self.chars: list[str] = [random.choice(_MATRIX_CHARS) for _ in range(self.length)]
        self.y = random.uniform(-h * 1.5, 0)
        self.h = h
        self.change_timer = 0

    def step(self):
        self.y += self.font_size * self.speed * 0.4
        if self.y > self.h + self.length * self.font_size:
            self.y = -self.length * self.font_size * random.uniform(1, 4)
            self.length = random.randint(8, 22)
            self.chars = [random.choice(_MATRIX_CHARS) for _ in range(self.length)]
            self.speed = random.uniform(1.0, 2.8)
        self.change_timer += 1
        if self.change_timer % 6 == 0:
            idx = random.randint(0, len(self.chars) - 1)
            self.chars[idx] = random.choice(_MATRIX_CHARS)


class BootScreen(QWidget):
    boot_complete = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(_WS_STYLED)
        self.setFixedSize(900, 620)

        # Center on screen
        if QApplication.primaryScreen():
            geo = QApplication.primaryScreen().geometry()
            self.move(
                (geo.width()  - self.width())  // 2,
                (geo.height() - self.height()) // 2,
            )

        self._matrix_cols: list[MatrixColumn] = []
        self._font_size = 14
        self._init_matrix()

        self._progress   = 0.0        # 0.0 → 1.0
        self._shown_lines: list[str] = []
        self._line_idx   = 0
        self._fade_in    = 0.0        # overall fade-in alpha
        self._fade_out   = 0.0        # final fade-out alpha (0=visible 1=gone)
        self._done       = False
        self._scan_y     = 0.0        # scanline

        self._tick_count = 0

        # Matrix anim
        self._matrix_timer = QTimer(self)
        self._matrix_timer.timeout.connect(self._tick_matrix)
        self._matrix_timer.start(28)

        # Boot sequence
        self._boot_timer = QTimer(self)
        self._boot_timer.timeout.connect(self._tick_boot)
        self._boot_timer.start(160)

        # Fade-in
        self._fade_in_timer = QTimer(self)
        self._fade_in_timer.timeout.connect(self._tick_fade_in)
        self._fade_in_timer.start(20)

    # ── Init ─────────────────────────────────────────────────────────────
    def _init_matrix(self):
        cols = self.width() // self._font_size
        for i in range(cols):
            self._matrix_cols.append(
                MatrixColumn(i * self._font_size, self.height(), self._font_size))

    # ── Ticks ─────────────────────────────────────────────────────────────
    def _tick_matrix(self):
        for c in self._matrix_cols:
            c.step()
        self._scan_y = (self._scan_y + 2.5) % self.height()
        self._tick_count += 1
        self.update()

    def _tick_boot(self):
        if self._done: return
        next_threshold = _BOOT_LINES[self._line_idx][1] if self._line_idx < len(_BOOT_LINES) else 1.0
        if self._progress >= next_threshold and self._line_idx < len(_BOOT_LINES):
            self._shown_lines.append(_BOOT_LINES[self._line_idx][0])
            self._line_idx += 1

        self._progress = min(1.0, self._progress + 0.013)

        if self._progress >= 1.0:
            self._done = True
            self._boot_timer.stop()
            QTimer.singleShot(600, self._start_fadeout)

    def _tick_fade_in(self):
        self._fade_in = min(1.0, self._fade_in + 0.06)
        if self._fade_in >= 1.0:
            self._fade_in_timer.stop()

    def _start_fadeout(self):
        t = QTimer(self)
        t.timeout.connect(self._tick_fadeout)
        t.start(18)
        self._fo_timer = t

    def _tick_fadeout(self):
        self._fade_out = min(1.0, self._fade_out + 0.05)
        self.update()
        if self._fade_out >= 1.0:
            self._fo_timer.stop()
            self._matrix_timer.stop()
            self.boot_complete.emit()

    # ── Paint ─────────────────────────────────────────────────────────────
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(_AA)
        p.setRenderHint(_TEXT)

        W, H = self.width(), self.height()
        global_alpha = self._fade_in * (1.0 - self._fade_out)
        p.setOpacity(global_alpha)

        # ── Background ──
        p.fillRect(0, 0, W, H, QColor(0, 4, 8))

        # ── Matrix rain ──
        mf = QFont("Courier New", self._font_size - 3)
        mf.setWeight(QFont.Weight.Bold)
        p.setFont(mf)
        for col in self._matrix_cols:
            for row_i, ch in enumerate(col.chars):
                row_y = int(col.y) + row_i * self._font_size
                if not (0 <= row_y <= H): continue
                dist = row_i / len(col.chars)
                if row_i == len(col.chars) - 1:
                    p.setPen(QColor(200, 255, 220, 240))   # head: bright
                elif row_i >= len(col.chars) - 3:
                    alpha = int(200 - (len(col.chars) - 1 - row_i) * 60)
                    p.setPen(QColor(0, 220, 100, alpha))
                else:
                    alpha = max(20, int(80 * (1 - dist)))
                    p.setPen(QColor(0, 140, 55, alpha))
                p.drawText(col.x, row_y, ch)

        # ── Scanline ──
        sg = QLinearGradient(0, self._scan_y - 18, 0, self._scan_y + 18)
        sg.setColorAt(0,   QColor(0, 255, 100, 0))
        sg.setColorAt(0.5, QColor(0, 255, 100, 22))
        sg.setColorAt(1,   QColor(0, 255, 100, 0))
        p.fillRect(0, int(self._scan_y) - 18, W, 36, sg)

        # ── Overlay panel ──
        p.fillRect(0, 0, W, H, QColor(0, 4, 12, 100))

        # ── Border frame ──
        pen = QPen(QColor(0, 200, 100, 160), 1.5)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush if hasattr(Qt, 'BrushStyle') else Qt.NoBrush)
        try:
            p.drawRect(14, 14, W - 28, H - 28)
        except: pass

        # Corner brackets
        blen = 22
        p.setPen(QPen(QColor(0, 255, 120, 220), 2.5))
        for cx, cy, dx, dy in [(14,14,1,1),(W-14,14,-1,1),(14,H-14,1,-1),(W-14,H-14,-1,-1)]:
            p.drawLine(cx, cy, cx + dx * blen, cy)
            p.drawLine(cx, cy, cx, cy + dy * blen)

        # ── Logo ──
        logo_f = QFont("Courier New", 36)
        logo_f.setWeight(QFont.Weight.Black)
        logo_f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10)
        p.setFont(logo_f)
        glow_a = int(140 + 60 * math.sin(self._tick_count * 0.07))
        p.setPen(QColor(0, 240, 140, glow_a))
        p.drawText(QRect(0, 40, W, 60), _ALIGN_C, "L · U · N · A")
        p.setPen(QColor(0, 255, 160, 255))
        p.drawText(QRect(2, 42, W, 60), _ALIGN_C, "L · U · N · A")

        sub_f = QFont("Courier New", 11)
        sub_f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        p.setFont(sub_f)
        p.setPen(QColor(0, 180, 100, 160))
        p.drawText(QRect(0, 100, W, 22), _ALIGN_C, "LANGUAGE UNDERSTANDING NEURAL AGENT  v5.0")

        # ── Divider ──
        p.setPen(QPen(QColor(0, 200, 100, 80), 1))
        p.drawLine(60, 130, W - 60, 130)

        # ── Boot log ──
        log_f = QFont("Courier New", 11)
        p.setFont(log_f)
        log_top = 148
        log_h   = 24
        visible_lines = self._shown_lines[-14:]
        for i, line in enumerate(visible_lines):
            y = log_top + i * log_h
            freshness = len(visible_lines) - i
            if freshness == 1:
                p.setPen(QColor(200, 255, 220, 255))  # latest
            elif freshness <= 3:
                p.setPen(QColor(0, 220, 110, 210))
            else:
                fade_a = max(100, 200 - freshness * 12)
                p.setPen(QColor(0, 160, 80, fade_a))
            p.drawText(QRect(60, y, W - 120, log_h), _ALIGN_L, line)

        # Blinking cursor on last line
        if not self._done and self._shown_lines:
            last_y = log_top + min(len(visible_lines), 14) * log_h - log_h
            if (self._tick_count // 12) % 2 == 0:
                p.setPen(QColor(0, 255, 140, 255))
                p.drawText(QRect(60, last_y, W - 120, log_h), _ALIGN_L, "█")

        # ── Progress bar ──
        bar_y = H - 80
        bar_w = W - 120
        bar_x = 60
        bar_h = 6

        # Track
        p.setPen(_NO_PEN)
        p.setBrush(QColor(0, 40, 20, 120))
        p.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 3, 3)

        # Fill
        fill_w = int(bar_w * self._progress)
        if fill_w > 0:
            grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
            grad.setColorAt(0,   QColor(0, 180, 80, 220))
            grad.setColorAt(0.6, QColor(0, 230, 120, 240))
            grad.setColorAt(1.0, QColor(80, 255, 160, 255))
            p.setBrush(grad)
            p.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 3, 3)

        # Glow head
        if fill_w > 4:
            hg = QLinearGradient(bar_x + fill_w - 20, 0, bar_x + fill_w + 4, 0)
            hg.setColorAt(0, QColor(100, 255, 180, 0))
            hg.setColorAt(1, QColor(200, 255, 220, 180))
            p.setBrush(hg)
            p.drawRoundedRect(bar_x + fill_w - 20, bar_y - 2, 24, bar_h + 4, 4, 4)

        # Percent
        pct_f = QFont("Courier New", 10)
        p.setFont(pct_f)
        p.setPen(QColor(0, 220, 110, 200))
        p.drawText(QRect(bar_x, bar_y + 10, bar_w, 20), _ALIGN_R,
                   f"{int(self._progress * 100):3d}%  LOADING")

        # ── Bottom label ──
        btm_f = QFont("Courier New", 9)
        p.setFont(btm_f)
        p.setPen(QColor(0, 140, 70, 120))
        p.drawText(QRect(0, H - 24, W, 20), _ALIGN_C,
                   "SECURED  ·  ENCRYPTED  ·  AI-POWERED  ·  © LUNA SYSTEMS")
