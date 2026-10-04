from collections import deque

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

TRACK = QColor("#2a2f3a")
ACCENT = QColor("#5b9cf5")


def level_color(pct: float) -> QColor:
    if pct < 60:
        return QColor("#4cc38a")
    if pct < 85:
        return QColor("#f0b429")
    return QColor("#ef5350")


class Gauge(QWidget):
    """Circular gauge, 0-100."""

    def __init__(self, size: int = 120, parent=None):
        super().__init__(parent)
        self.value, self.caption = 0.0, ""
        self.setMinimumSize(size, size)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def set_value(self, value: float, caption: str = "") -> None:
        self.value, self.caption = max(0.0, min(100.0, value)), caption
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height()) - 12
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        pen = QPen(TRACK, 9, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 225 * 16, -270 * 16)
        pen.setColor(level_color(self.value))
        p.setPen(pen)
        p.drawArc(rect, 225 * 16, int(-270 * 16 * self.value / 100))
        p.setPen(QColor("#e6e9ef"))
        f = QFont(self.font())
        f.setPixelSize(max(12, int(side * 0.22)))
        f.setBold(True)
        p.setFont(f)
        p.drawText(rect.adjusted(0, -side * 0.06 if self.caption else 0, 0, -side * 0.06 if self.caption else 0),
                   Qt.AlignCenter, f"{self.value:.0f}%")
        if self.caption:
            f.setPixelSize(max(9, int(side * 0.09)))
            f.setBold(False)
            p.setFont(f)
            p.setPen(QColor("#8b93a5"))
            p.drawText(rect.adjusted(0, side * 0.60, 0, 0), Qt.AlignHCenter | Qt.AlignTop, self.caption)


class Bar(QWidget):
    """Horizontal usage bar, 0-100."""

    def __init__(self, height: int = 8, parent=None):
        super().__init__(parent)
        self.value = 0.0
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, value: float) -> None:
        self.value = max(0.0, min(100.0, value))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.NoPen)
        p.setBrush(TRACK)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        p.setBrush(level_color(self.value))
        p.drawRoundedRect(QRectF(0, 0, max(r.height(), r.width() * self.value / 100), r.height()),
                          r.height() / 2, r.height() / 2)


class Sparkline(QWidget):
    """Scrolling history line. Fixed 0-100 scale unless `auto_scale`."""

    def __init__(self, points: int = 60, auto_scale: bool = False, color: QColor = ACCENT, parent=None):
        super().__init__(parent)
        self.data = deque([0.0] * points, maxlen=points)
        self.auto_scale, self.color = auto_scale, QColor(color)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def push(self, value: float) -> None:
        self.data.append(value)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height() - 2
        top = max(max(self.data), 1.0) * 1.1 if self.auto_scale else 100.0
        n = len(self.data)
        pts = [QPointF(i * w / (n - 1), 1 + h - h * min(v, top) / top) for i, v in enumerate(self.data)]
        line = QPainterPath(pts[0])
        for pt in pts[1:]:
            line.lineTo(pt)
        fill = QPainterPath(line)
        fill.lineTo(w, h + 1)
        fill.lineTo(0, h + 1)
        fill.closeSubpath()
        c = QColor(self.color)
        c.setAlpha(45)
        p.fillPath(fill, c)
        p.setPen(QPen(self.color, 1.5))
        p.drawPath(line)
