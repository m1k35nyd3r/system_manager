"""Public plugin API: subclass DashboardWidget in any .py file dropped into the user widgets folder."""
from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QPainter
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout, QWidget

from .gauges import ACCENT, Bar, Gauge, Sparkline, level_color  # noqa: F401  (re-exported for plugins)
from .stats import Stats, fmt_bytes  # noqa: F401


CARD_MIME = "application/x-systemmanager-card"


class _ResizeGrip(QWidget):
    """Bottom-right handle; reports the global pointer position while dragged."""

    def __init__(self, card: "DashboardWidget"):
        super().__init__(card)
        self.card = card
        self.setFixedSize(18, 18)
        self.setCursor(Qt.SizeFDiagCursor)
        self.setToolTip("Drag to resize")

    def mousePressEvent(self, e):
        e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self.card.resizing.emit(e.globalPosition().toPoint())

    def mouseReleaseEvent(self, e):
        self.card.resize_done.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4a5163"))
        for i in range(3):
            for j in range(3 - i):
                p.drawEllipse(self.width() - 5 - j * 4, self.height() - 5 - i * 4, 2, 2)


class DashboardWidget(QFrame):
    id: str = ""          # unique key, stored in config
    title: str = ""       # card heading
    interval: float = 1   # seconds between update_data() calls
    supported: bool = True  # set False (e.g. wrong OS) to keep the widget out of the + Widgets menu
    span: int = 1         # default grid columns the card occupies (the user can resize it)

    resizing = Signal(QPoint)   # global pointer position while the resize grip is dragged
    resize_done = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(16, 12, 16, 14)
        self.body.setSpacing(10)
        self._heading = QLabel(self.title or self.id)
        self._heading.setObjectName("cardTitle")
        self._heading.setCursor(Qt.OpenHandCursor)
        self.body.addWidget(self._heading)
        self._drag_start: QPoint | None = None
        self.new_row = False  # user pinned: always start this card on a fresh grid row
        self.height_override: int | None = None  # set when the user resizes the card taller/shorter
        self.setup(self.body)
        self.body.addStretch(1)  # extra height from resizing goes below the content
        self._grip = _ResizeGrip(self)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._grip.move(self.width() - self._grip.width() - 3, self.height() - self._grip.height() - 3)
        self._grip.raise_()

    # Dragging the heading reorders the card (the dashboard grid handles the drop).
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self._heading.geometry().adjusted(0, -12, 0, 6).contains(e.position().toPoint()):
            self._drag_start = e.position().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if (self._drag_start is not None and e.buttons() & Qt.LeftButton
                and (e.position().toPoint() - self._drag_start).manhattanLength() >= QApplication.startDragDistance()):
            self._drag_start = None
            mime = QMimeData()
            mime.setData(CARD_MIME, self.id.encode())
            drag = QDrag(self)
            drag.setMimeData(mime)
            pix = self.grab().scaledToWidth(min(self.width(), 260), Qt.SmoothTransformation)
            drag.setPixmap(pix)
            drag.setHotSpot(QPoint(pix.width() // 2, 16))
            drag.exec(Qt.MoveAction)
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_start = None
        super().mouseReleaseEvent(e)

    def setup(self, layout: QVBoxLayout) -> None:
        """Add child widgets to `layout`."""

    def update_data(self, stats: Stats) -> None:
        """Called every `interval` seconds."""
