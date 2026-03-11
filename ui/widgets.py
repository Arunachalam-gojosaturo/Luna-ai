import math, random, psutil

try:
    from PyQt6.QtWidgets import QWidget
    from PyQt6.QtCore    import Qt, QTimer, QRect, QPointF
    from PyQt6.QtGui     import (QPainter, QColor, QPen, QBrush,
                                  QRadialGradient, QLinearGradient, QFont, QPolygonF)
    _AA    = QPainter.RenderHint.Antialiasing
    _TEXT  = QPainter.RenderHint.TextAntialiasing
    _NO_PEN   = Qt.PenStyle.NoPen
    _NO_BRUSH = Qt.BrushStyle.NoBrush
    _ROUND    = Qt.PenCapStyle.RoundCap
    _CENTER   = Qt.AlignmentFlag.AlignCenter
except ImportError:
    from PyQt5.QtWidgets import QWidget
    from PyQt5.QtCore    import Qt, QTimer, QRect, QPointF
    from PyQt5.QtGui     import (QPainter, QColor, QPen, QBrush,
                                  QRadialGradient, QLinearGradient, QFont, QPolygonF)
    _AA    = QPainter.Antialiasing
    _TEXT  = QPainter.TextAntialiasing
    _NO_PEN   = Qt.NoPen
    _NO_BRUSH = Qt.NoBrush
    _ROUND    = Qt.RoundCap
    _CENTER   = Qt.AlignCenter

_STATE_RGB = {
    "READY":     (0,  220, 140),
    "THINKING":  (255,185,  0),
    "SPEAKING":  (0,  180, 255),
    "LISTENING": (180, 55, 255),
    "BOOTING":   ( 60, 80, 110),
    "WORKING":   (255,120,  0),
    "ERROR":     (255, 55, 55),
}


# ── Status Dot ───────────────────────────────────────────────────────────────
class StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._state = "BOOTING"
        self._pulse = 0.0; self._dir = 1
        t = QTimer(self); t.timeout.connect(self._tick); t.start(35)

    def set_state(self, s): self._state = s

    def _tick(self):
        self._pulse += 0.07 * self._dir
        if self._pulse >= 1: self._dir = -1
        elif self._pulse <= 0: self._dir = 1
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(_AA)
        r, g, b = _STATE_RGB.get(self._state, (60,80,110))
        p.setPen(_NO_PEN)
        p.setBrush(QColor(r,g,b, int(45+70*self._pulse)))
        p.drawEllipse(0,0,14,14)
        p.setBrush(QColor(r,g,b,245))
        p.drawEllipse(3,3,8,8)


# ── HUD Arc Widget ───────────────────────────────────────────────────────────
class HUDWidget(QWidget):
    _LABELS = {
        "READY":"●  READY","THINKING":"◈  THINKING","SPEAKING":"◉  SPEAKING",
        "LISTENING":"◎  LISTENING","BOOTING":"◌  BOOTING",
        "WORKING":"⚙  WORKING","ERROR":"✖  ERROR",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self._state = "BOOTING"; self._angle = 0.0
        self._pulse = 0.0; self._pdir = 1
        self._particles: list[dict] = []
        t = QTimer(self); t.timeout.connect(self._tick); t.start(22)

    def set_state(self, s):
        self._state = s
        if s in ("THINKING","SPEAKING","LISTENING","WORKING"):
            self._spawn_particles(8)

    def _spawn_particles(self, n):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            r, g, b = _STATE_RGB.get(self._state, (60,80,110))
            self._particles.append({
                "a": a, "r": random.uniform(0.55, 0.82),
                "life": 1.0, "speed": random.uniform(0.008, 0.025),
                "rgb": (r, g, b)
            })

    def _tick(self):
        spd = {"THINKING":3.5,"SPEAKING":2.2,"LISTENING":5.0,"WORKING":4.0}.get(self._state,0.7)
        self._angle = (self._angle + spd) % 360
        self._pulse += 0.045 * self._pdir
        if self._pulse >= 1: self._pdir = -1
        elif self._pulse <= 0: self._pdir = 1
        for pt in self._particles:
            pt["r"]    += pt["speed"]
            pt["life"] -= 0.022
        self._particles = [pt for pt in self._particles if pt["life"] > 0]
        if self._state in ("THINKING","LISTENING","WORKING") and random.random() < 0.25:
            self._spawn_particles(2)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(_AA); p.setRenderHint(_TEXT)
        w, h = self.width(), self.height()
        cx, cy = w//2, h//2 - 8
        br = min(w,h)//2 - 18
        r, g, b = _STATE_RGB.get(self._state, (60,80,110))
        col = QColor(r,g,b)

        # Bg circle
        p.setPen(_NO_PEN)
        rg = QRadialGradient(cx, cy, br+12)
        rg.setColorAt(0, QColor(r,g,b,18))
        rg.setColorAt(1, QColor(0,0,0,0))
        p.setBrush(rg); p.drawEllipse(cx-br-12,cy-br-12,(br+12)*2,(br+12)*2)

        # Dashed outer ring
        dash = QPen(QColor(r,g,b,50),1)
        try: dash.setStyle(Qt.PenStyle.DashLine)
        except: dash.setStyle(Qt.DashLine)
        p.setPen(dash); p.setBrush(_NO_BRUSH)
        p.drawEllipse(cx-br,cy-br,br*2,br*2)

        # Tick marks
        p.setPen(QPen(QColor(r,g,b,55),1))
        for i in range(36):
            a = math.radians(i*10)
            inner = br-5 if i%3==0 else br-3
            p.drawLine(int(cx+inner*math.cos(a)), int(cy+inner*math.sin(a)),
                       int(cx+br*math.cos(a)),    int(cy+br*math.sin(a)))

        # Spinning arcs (outer)
        for i in range(5):
            a = int(self._angle*16) + i*(72*16)
            alpha = int(60+190*(i+1)/5)
            pk = QPen(QColor(r,g,b,alpha),2.5); pk.setCapStyle(_ROUND)
            p.setPen(pk)
            p.drawArc(QRect(cx-br,cy-br,br*2,br*2), a, 48*16)

        # Counter arcs (inner)
        r2 = br-20
        for i in range(3):
            a = int(-self._angle*1.5*16)+i*(120*16)
            alpha = int(80+155*(i+1)/3)
            pk = QPen(QColor(r,g,b,alpha),1.8); pk.setCapStyle(_ROUND)
            p.setPen(pk)
            p.drawArc(QRect(cx-r2,cy-r2,r2*2,r2*2), a, 70*16)

        # Particles
        for pt in self._particles:
            px = cx + pt["r"]*br*math.cos(pt["a"])
            py = cy + pt["r"]*br*math.sin(pt["a"])
            a  = int(pt["life"]*200)
            pr, pg, pb = pt["rgb"]
            p.setPen(_NO_PEN)
            p.setBrush(QColor(pr,pg,pb,a))
            sz = int(pt["life"]*4)+1
            p.drawEllipse(int(px)-sz,int(py)-sz,sz*2,sz*2)

        # Centre glow
        gr = int(22+9*self._pulse)
        grad = QRadialGradient(cx,cy,gr)
        grad.setColorAt(0,   QColor(r,g,b,230))
        grad.setColorAt(0.4, QColor(r,g,b,100))
        grad.setColorAt(1,   QColor(r,g,b,0))
        p.setPen(_NO_PEN); p.setBrush(grad)
        p.drawEllipse(cx-gr,cy-gr,gr*2,gr*2)
        p.setBrush(QColor(r,g,b,255))
        p.drawEllipse(cx-5,cy-5,10,10)

        # State label
        lf = QFont("Consolas",9)
        p.setFont(lf)
        p.setPen(QColor(r,g,b,180))
        label = self._LABELS.get(self._state, self._state)
        p.drawText(QRect(0,cy+br-2,w,22), _CENTER, label)


# ── Voice Visualizer ─────────────────────────────────────────────────────────
class VoiceVisualizer(QWidget):
    BARS = 32
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._active = False
        self._bars   = [0.06]*self.BARS
        self._tgt    = [0.06]*self.BARS
        t = QTimer(self); t.timeout.connect(self._tick); t.start(30)

    def start(self): self._active = True
    def stop(self):  self._active = False

    def _tick(self):
        for i in range(self.BARS):
            if self._active:
                center = abs(i - self.BARS//2) / (self.BARS//2)
                self._tgt[i] = random.uniform(0.1, 1.0) * (1 - center*0.4)
            else:
                self._tgt[i] = random.uniform(0.03, 0.10)
            self._bars[i] += (self._tgt[i]-self._bars[i])*0.20
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(_AA)
        w, h = self.width(), self.height()
        n = self.BARS
        gap = 2
        bw = max(2,(w-n*gap)//n)
        sx = (w-n*(bw+gap))//2
        for i, v in enumerate(self._bars):
            bh = max(3, int(v*(h-8)))
            x = sx+i*(bw+gap); y=(h-bh)//2
            t = i/n
            r2 = int(0+60*t); g2 = int(160+95*(1-abs(t-0.5)*2)); b2 = int(220+35*(1-t))
            p.setPen(_NO_PEN)
            p.setBrush(QColor(r2,g2,b2,int(130+120*v)))
            p.drawRoundedRect(x,y,bw,bh,2,2)


# ── System Meters ─────────────────────────────────────────────────────────────
class SystemMeter(QWidget):
    """CPU / RAM / Disk animated arc gauges."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(88)
        self._cpu  = 0.0; self._ram = 0.0; self._disk = 0.0
        self._tcpu = 0.0; self._tram = 0.0; self._tdisk = 0.0
        t = QTimer(self); t.timeout.connect(self._tick); t.start(1500)
        self._fetch()

    def _fetch(self):
        self._tcpu  = psutil.cpu_percent()/100
        self._tram  = psutil.virtual_memory().percent/100
        self._tdisk = psutil.disk_usage("/").percent/100

    def _tick(self):
        self._fetch()
        smooth = 0.25
        self._cpu  += (self._tcpu  - self._cpu)  * smooth
        self._ram  += (self._tram  - self._ram)  * smooth
        self._disk += (self._tdisk - self._disk) * smooth
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(_AA); p.setRenderHint(_TEXT)
        w, h = self.width(), self.height()
        items = [("CPU", self._cpu, (0,200,120)),
                 ("RAM", self._ram, (0,160,255)),
                 ("DSK", self._disk,(200,120,0))]
        slot = w//3
        for idx,(label, val, rgb) in enumerate(items):
            cx = slot*idx + slot//2
            cy = h//2
            rad = min(slot,h)//2 - 10
            r, g, b = rgb

            # Bg arc
            p.setPen(QPen(QColor(r,g,b,30),4))
            p.setBrush(_NO_BRUSH)
            p.drawArc(QRect(cx-rad,cy-rad,rad*2,rad*2), 30*16, 120*16)

            # Value arc
            span = int(val*120*16)
            if span > 0:
                col = QColor(r,g,b,200)
                if val > 0.85: col = QColor(255,80,80,230)
                elif val > 0.65: col = QColor(255,180,0,230)
                p.setPen(QPen(col,4)); p.setPen(QPen(col,4))
                try:  p.setPen(QPen(col,4,cap=_ROUND))
                except: pass
                p.drawArc(QRect(cx-rad,cy-rad,rad*2,rad*2), 30*16, span)

            # Label
            lf = QFont("Consolas",8)
            p.setFont(lf)
            p.setPen(QColor(r,g,b,150))
            p.drawText(QRect(cx-rad,cy-6,rad*2,14), _CENTER, label)
            p.setPen(QColor(r,g,b,240))
            pf = QFont("Consolas",9); pf.setBold(True)
            p.setFont(pf)
            p.drawText(QRect(cx-rad,cy+6,rad*2,14), _CENTER, f"{int(val*100)}%")
