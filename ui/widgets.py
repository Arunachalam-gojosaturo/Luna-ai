"""Luna AI v6 — UI Widgets"""
import math, psutil, random

try:
    from PyQt6.QtWidgets import QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout
    from PyQt6.QtCore    import Qt, QTimer, pyqtSignal
    from PyQt6.QtGui     import QPainter, QColor, QFont, QLinearGradient, QPen, QBrush
    _Q6 = True
    _AC  = Qt.AlignmentFlag.AlignCenter
    _AL  = Qt.AlignmentFlag.AlignLeft
    _AR  = Qt.AlignmentFlag.AlignRight
except ImportError:
    from PyQt5.QtWidgets import QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout
    from PyQt5.QtCore    import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui     import QPainter, QColor, QFont, QLinearGradient, QPen, QBrush
    _Q6 = False
    _AC  = Qt.AlignCenter
    _AL  = Qt.AlignLeft
    _AR  = Qt.AlignRight

CYAN   = QColor(0, 200, 255)
VIOLET = QColor(124, 58, 237)
GREEN  = QColor(52, 211, 153)
RED    = QColor(248, 113, 113)
DARK   = QColor(14, 15, 26)
BORDER = QColor(30, 32, 53)


# ── Status Dot ────────────────────────────────────────────────────────────────
class StatusDot(QWidget):
    _COLORS = {
        "READY":     QColor(52, 211, 153),
        "THINKING":  QColor(251, 191, 36),
        "SPEAKING":  QColor(0, 200, 255),
        "LISTENING": QColor(124, 58, 237),
        "WORKING":   QColor(251, 146, 60),
        "ERROR":     QColor(248, 113, 113),
        "BOOTING":   QColor(100, 116, 139),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._color = QColor(100, 116, 139)
        self._pulse = 0.0
        self._t = QTimer(self); self._t.timeout.connect(self._tick); self._t.start(40)

    def set_state(self, state: str):
        self._color = self._COLORS.get(state.upper(), QColor(100, 116, 139))
        self.update()

    def _tick(self):
        self._pulse = (self._pulse + 0.12) % (2 * math.pi)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing if _Q6 else QPainter.Antialiasing)
        glow = int(30 + 20 * math.sin(self._pulse))
        gc = QColor(self._color); gc.setAlpha(glow)
        p.setPen(Qt.PenStyle.NoPen if _Q6 else Qt.NoPen)
        p.setBrush(QBrush(gc))
        p.drawEllipse(0, 0, 14, 14)
        p.setBrush(QBrush(self._color))
        p.drawEllipse(3, 3, 8, 8)
        p.end()


# ── HUD (animated arc reactor style) ─────────────────────────────────────────
class HUDWidget(QWidget):
    _STATE_COLORS = {
        "READY":     (QColor(52, 211, 153),  QColor(0, 80, 60)),
        "THINKING":  (QColor(251, 191, 36),  QColor(80, 60, 0)),
        "SPEAKING":  (QColor(0, 200, 255),   QColor(0, 50, 80)),
        "LISTENING": (QColor(124, 58, 237),  QColor(40, 0, 80)),
        "WORKING":   (QColor(251, 146, 60),  QColor(80, 40, 0)),
        "ERROR":     (QColor(248, 113, 113), QColor(80, 0, 0)),
        "BOOTING":   (QColor(100, 116, 139), QColor(20, 20, 30)),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(190)
        self._angle  = 0.0
        self._state  = "BOOTING"
        self._rings  = [0.0, 0.0, 0.0]
        self._t = QTimer(self); self._t.timeout.connect(self._tick); self._t.start(33)

    def set_state(self, s: str):
        self._state = s.upper()
        self.update()

    def _tick(self):
        self._angle = (self._angle + 2.4) % 360
        for i in range(3):
            self._rings[i] = (self._rings[i] + [1.8, 2.8, 4.0][i]) % 360
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing if _Q6 else QPainter.Antialiasing)

        cx, cy = self.width() // 2, self.height() // 2
        r = min(cx, cy) - 12

        accent, glow_c = self._STATE_COLORS.get(self._state,
                         self._STATE_COLORS["BOOTING"])

        # Background circle
        p.setPen(Qt.PenStyle.NoPen if _Q6 else Qt.NoPen)
        p.setBrush(QBrush(QColor(14, 15, 26)))
        p.drawEllipse(cx - r, cy - r, 2*r, 2*r)

        # Rotating arcs
        pen = QPen(accent, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap if _Q6 else Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush if _Q6 else Qt.NoBrush)

        for i, span in enumerate([120, 90, 60]):
            rr = r - i * 14
            if rr < 10: continue
            a_c = QColor(accent); a_c.setAlpha(200 - i * 50)
            pp  = QPen(a_c, 2 - i * 0.4)
            pp.setCapStyle(Qt.PenCapStyle.RoundCap if _Q6 else Qt.RoundCap)
            p.setPen(pp)
            start = int((self._rings[i] + i * 60) * 16)
            p.drawArc(cx - rr, cy - rr, 2*rr, 2*rr, start, span * 16)

        # Center dot
        p.setPen(Qt.PenStyle.NoPen if _Q6 else Qt.NoPen)
        gc = QColor(accent); gc.setAlpha(40)
        p.setBrush(QBrush(gc))
        p.drawEllipse(cx - 28, cy - 28, 56, 56)
        p.setBrush(QBrush(accent))
        p.drawEllipse(cx - 8, cy - 8, 16, 16)

        # State label
        p.setPen(QPen(accent))
        font = QFont("JetBrains Mono", 9)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing if _Q6
                             else QFont.AbsoluteSpacing, 3)
        font.setBold(True)
        p.setFont(font)
        p.drawText(0, cy + r - 4, self.width(), 20, _AC, self._state)
        p.end()


# ── Voice Visualizer ─────────────────────────────────────────────────────────
class VoiceVisualizer(QWidget):
    _BAR_COUNT = 24

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self._active = False
        self._bars   = [0.0] * self._BAR_COUNT
        self._targets= [0.0] * self._BAR_COUNT
        self._t = QTimer(self); self._t.timeout.connect(self._tick); self._t.start(50)

    def start(self):
        self._active = True

    def stop(self):
        self._active = False

    def _tick(self):
        if self._active:
            for i in range(self._BAR_COUNT):
                if random.random() < 0.3:
                    self._targets[i] = random.uniform(0.15, 1.0)
        else:
            for i in range(self._BAR_COUNT):
                self._targets[i] *= 0.6
        for i in range(self._BAR_COUNT):
            diff = self._targets[i] - self._bars[i]
            self._bars[i] += diff * 0.35
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing if _Q6 else QPainter.Antialiasing)

        w, h = self.width(), self.height()
        bw   = w / self._BAR_COUNT
        mid  = h / 2

        for i, v in enumerate(self._bars):
            bh   = max(2.0, v * mid)
            x    = i * bw + bw * 0.15
            bww  = bw * 0.7
            grad = QLinearGradient(x, mid - bh, x, mid + bh)
            t    = i / self._BAR_COUNT
            r = int(0 + t * 124)
            g = int(200 - t * 80)
            b = int(255 - t * 18)
            c = QColor(r, g, b, 200)
            grad.setColorAt(0, c)
            grad.setColorAt(0.5, QColor(r, g, b, 255))
            grad.setColorAt(1, c)
            p.setPen(Qt.PenStyle.NoPen if _Q6 else Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(int(x), int(mid - bh), int(bww), int(bh * 2), 2, 2)
        p.end()


# ── System Meter ─────────────────────────────────────────────────────────────
class SystemMeter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self._cpu = 0; self._ram = 0; self._disk = 0
        self._t = QTimer(self); self._t.timeout.connect(self._update); self._t.start(2000)
        self._update()

    def _update(self):
        try:
            self._cpu  = psutil.cpu_percent(interval=None)
            self._ram  = psutil.virtual_memory().percent
            self._disk = psutil.disk_usage('/').percent
        except Exception:
            pass
        self.update()

    def _bar_color(self, pct):
        if pct > 85: return QColor(248, 113, 113)
        if pct > 60: return QColor(251, 191, 36)
        return QColor(52, 211, 153)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing if _Q6 else QPainter.Antialiasing)
        w = self.width()
        metrics = [("CPU", self._cpu), ("RAM", self._ram), ("DSK", self._disk)]
        row_h = self.height() // 3

        p.setFont(QFont("JetBrains Mono", 9))
        for i, (label, pct) in enumerate(metrics):
            y    = i * row_h + 3
            bar_y= y + 10
            col  = self._bar_color(pct)
            # Label
            p.setPen(QPen(QColor(100, 116, 139)))
            p.drawText(0, y, 32, 12, _AL, label)
            # Pct
            p.setPen(QPen(col))
            p.drawText(w - 40, y, 40, 12, _AR, f"{pct:.0f}%")
            # Track
            p.setPen(Qt.PenStyle.NoPen if _Q6 else Qt.NoPen)
            p.setBrush(QBrush(QColor(30, 32, 53)))
            p.drawRoundedRect(34, bar_y, w - 76, 5, 2, 2)
            # Fill
            fill_w = int((w - 76) * pct / 100)
            if fill_w > 0:
                p.setBrush(QBrush(col))
                p.drawRoundedRect(34, bar_y, fill_w, 5, 2, 2)
        p.end()
