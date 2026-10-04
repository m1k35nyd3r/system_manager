import logging
import sys
import time

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QCursor, QDesktopServices, QPainter
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel, QMenu, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from . import config
from .api import CARD_MIME, DashboardWidget
from .loader import Registry
from .stats import Stats
from .style import QSS

log = logging.getLogger("systemmanager")
MIN_CARD_WIDTH = 320
EDGE = 7
SPACING = 14
MIN_CARD_HEIGHT = 80


class Grid(QWidget):
    """Lays cards out in as many equal columns as fit, honouring each card's span."""

    reordered = Signal(str, int)  # dragged card id, index among the other visible cards

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self._drop: tuple[int, int, int] | None = None  # drop indicator (x, y, height)
        self.cards: list[DashboardWidget] = []
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(SPACING)
        self._cols = 0
        self._viewport: QWidget | None = None

    def track_viewport(self, viewport: QWidget) -> None:
        """Columns are chosen from the visible area, not our own width (which cards' minimum sizes can prop up)."""
        self._viewport = viewport
        viewport.installEventFilter(self)

    def eventFilter(self, obj, e):
        if obj is self._viewport and e.type() == QEvent.Resize:
            self.relayout()
        return False

    def _available_width(self) -> int:
        return self._viewport.width() if self._viewport else self.width()

    def _column_min_width(self) -> int:
        return max([MIN_CARD_WIDTH] + [c.minimumSizeHint().width() for c in self.cards])

    def resize_card(self, card: DashboardWidget, global_pos: QPoint) -> None:
        """Live-resize `card` so its bottom-right corner follows the pointer: width snaps to columns."""
        cols = max(1, self._cols)
        colw = (self._available_width() - SPACING * (cols - 1)) / cols
        local = self.mapFromGlobal(global_pos)
        card.span = max(1, min(cols, round((local.x() - card.x() + SPACING) / (colw + SPACING))))
        card.height_override = max(local.y() - card.y(), MIN_CARD_HEIGHT)
        self.relayout(force=True)

    def set_cards(self, cards: list[DashboardWidget]) -> None:
        self.cards = cards
        self.relayout(force=True)

    def relayout(self, force: bool = False) -> None:
        cols = max(1, (self._available_width() + SPACING) // (self._column_min_width() + SPACING))
        if cols == self._cols and not force:
            return
        self._cols = cols
        while self.grid.count():
            self.grid.takeAt(0)
        for c in range(self.grid.columnCount()):  # clear stretch left over from a previous column count
            self.grid.setColumnStretch(c, 0)
        for r in range(self.grid.rowCount()):
            self.grid.setRowStretch(r, 0)
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)
        row = col = 0
        for card in self.cards:
            if card.height_override is None:
                card.setMinimumHeight(0)
                card.setMaximumHeight(16777215)
            else:  # never shrink below what the content needs
                card.setFixedHeight(max(card.height_override, card.minimumSizeHint().height()))
            span = min(card.span, cols)
            if card.new_row and col > 0:
                row, col = row + 1, 0
            if col + span > cols:
                row, col = row + 1, 0
            self.grid.addWidget(card, row, col, 1, span, Qt.AlignTop)
            card.show()
            col += span
            if col >= cols:
                row, col = row + 1, 0
        self.grid.setRowStretch(row + 1, 1)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.relayout()

    # --- drag-to-reorder -------------------------------------------------
    def _target(self, pos: QPoint, dragged: str):
        """(index among the other cards, reference card, insert-after?) for a pointer position."""
        others = [c for c in self.cards if c.id != dragged]
        if not others:
            return 0, None, False
        i = min(range(len(others)), key=lambda k: (others[k].geometry().center() - pos).manhattanLength())
        after = pos.x() > others[i].geometry().center().x()
        return i + after, others[i], after

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(CARD_MIME):
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        dragged = bytes(e.mimeData().data(CARD_MIME)).decode()
        _, ref, after = self._target(e.position().toPoint(), dragged)
        if ref is not None:
            g = ref.geometry()
            self._drop = (g.right() + 7 if after else g.left() - 7, g.top(), g.height())
        self.update()
        e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        self._drop = None
        self.update()

    def dropEvent(self, e):
        dragged = bytes(e.mimeData().data(CARD_MIME)).decode()
        index, _, _ = self._target(e.position().toPoint(), dragged)
        self._drop = None
        self.update()
        e.acceptProposedAction()
        self.reordered.emit(dragged, index)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._drop:
            x, y, h = self._drop
            p = QPainter(self)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#5b9cf5"))
            p.drawRoundedRect(x - 2, y, 4, h, 2, 2)


class TitleBar(QWidget):
    def __init__(self, window: "Dashboard"):
        super().__init__()
        self.setObjectName("titlebar")
        self.win = window
        self._drag_offset: QPoint | None = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 6, 8, 6)
        title = QLabel("System Manager")
        title.setObjectName("appTitle")
        self.status = QLabel()
        self.status.setObjectName("error")
        lay.addWidget(title)
        lay.addWidget(self.status)
        lay.addStretch(1)
        self.add_btn = QPushButton("+ Widgets")
        self.add_btn.clicked.connect(window.show_widget_menu)
        lay.addWidget(self.add_btn)
        for text, slot, name in (("—", window.showMinimized, ""), ("▢", window.toggle_max, ""),
                                 ("✕", window.close, "closeBtn")):
            b = QPushButton(text)
            b.setObjectName(name)
            b.clicked.connect(slot)
            lay.addWidget(b)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and not self.win.windowHandle().startSystemMove():
            # No native move on this platform: drag the window ourselves.
            self._drag_offset = e.globalPosition().toPoint() - self.win.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_offset is not None and e.buttons() & Qt.LeftButton:
            self.win.move(e.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, e):
        self._drag_offset = None

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.win.toggle_max()


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Manager")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(440, 300)
        self._resize: tuple[Qt.Edges, QPoint, QRect] | None = None

        self.cfg = config.load()
        self.stats = Stats()
        self.registry = Registry()
        self.registry.changed.connect(self.on_registry_changed)
        self.instances: dict[str, DashboardWidget] = {}
        self._last_run: dict[str, float] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(EDGE, EDGE, EDGE, EDGE)
        root = QWidget()
        root.setObjectName("root")
        outer.addWidget(root)
        col = QVBoxLayout(root)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        self.titlebar = TitleBar(self)
        col.addWidget(self.titlebar)
        self.grid = Grid()
        self.grid.reordered.connect(self.move_to)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self.grid)
        self.grid.track_viewport(scroll.viewport())
        wrap = QVBoxLayout()
        wrap.setContentsMargins(14, 14, 6, 14)
        wrap.addWidget(scroll)
        col.addLayout(wrap)

        x, y, w, h = self.cfg["geometry"]
        self.setGeometry(x, y, w, h)
        # The window's current size becomes the next start-up size, saved shortly after you stop resizing.
        self._geom_timer = QTimer(self, singleShot=True, interval=500)
        self._geom_timer.timeout.connect(self.save_geometry)
        self.rebuild()

        self.timer = QTimer(self, interval=1000)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.tick()

    # --- widgets ---------------------------------------------------------
    def rebuild(self) -> None:
        """Make instances match cfg['enabled'] (and the current classes), preserving order."""
        enabled = [i for i in self.cfg["enabled"] if i in self.registry.classes]
        for wid, inst in list(self.instances.items()):
            if wid not in enabled or type(inst) is not self.registry.classes[wid]:
                self.instances.pop(wid)
                self._last_run.pop(wid, None)
                inst.setParent(None)
                inst.deleteLater()
        for wid in enabled:
            if wid not in self.instances:
                inst = self.registry.classes[wid]()
                size = self.cfg["sizes"].get(wid, {})
                inst.span = size.get("span", inst.span)
                inst.height_override = size.get("height")
                inst.new_row = wid in self.cfg["new_row"]
                inst.resizing.connect(lambda gpos, w=wid: self.grid.resize_card(self.instances[w], gpos))
                inst.resize_done.connect(lambda w=wid: self.save_size(w))
                inst.setContextMenuPolicy(Qt.CustomContextMenu)
                inst.customContextMenuRequested.connect(lambda _pos, w=wid: self.card_menu(w))
                self.instances[wid] = inst
        self.grid.set_cards([self.instances[i] for i in enabled])
        errs = self.registry.errors
        self.titlebar.status.setText(f"⚠ {len(errs)} plugin error(s)" if errs else "")
        self.titlebar.status.setToolTip("\n".join(f"{p.name}: {m}" for p, m in errs.items()))

    def on_registry_changed(self) -> None:
        self.rebuild()
        self.tick()

    def tick(self) -> None:
        self.stats.advance()
        now = time.monotonic()
        for wid, inst in self.instances.items():
            if now - self._last_run.get(wid, 0) < inst.interval - 0.05:
                continue
            self._last_run[wid] = now
            try:
                inst.update_data(self.stats)
            except Exception:
                log.exception("widget %s failed in update_data", wid)

    def show_widget_menu(self) -> None:
        menu = QMenu(self)
        for wid, cls in sorted(self.registry.classes.items(), key=lambda kv: kv[1].title or kv[0]):
            act = QAction(cls.title or wid, menu, checkable=True, checked=wid in self.cfg["enabled"])
            act.toggled.connect(lambda on, w=wid: self.set_enabled(w, on))
            menu.addAction(act)
        menu.addSeparator()
        menu.addAction("Open widgets folder", lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(config.USER_WIDGETS_DIR))))
        menu.exec(self.titlebar.add_btn.mapToGlobal(QPoint(0, self.titlebar.add_btn.height())))

    def set_enabled(self, wid: str, on: bool) -> None:
        enabled = self.cfg["enabled"]
        if on and wid not in enabled:
            enabled.append(wid)
        elif not on and wid in enabled:
            enabled.remove(wid)
        self.rebuild()
        self.tick()

    def save_size(self, wid: str) -> None:
        inst = self.instances[wid]
        self.cfg["sizes"][wid] = {"span": inst.span, "height": inst.height_override}
        config.save(self.cfg)

    def set_new_row(self, wid: str, on: bool) -> None:
        self.instances[wid].new_row = on
        rows = self.cfg["new_row"]
        if on and wid not in rows:
            rows.append(wid)
        elif not on and wid in rows:
            rows.remove(wid)
        config.save(self.cfg)
        self.grid.relayout(force=True)

    def reset_size(self, wid: str) -> None:
        inst = self.instances[wid]
        inst.span, inst.height_override = type(inst).span, None
        self.cfg["sizes"].pop(wid, None)
        self.grid.relayout(force=True)

    def card_menu(self, wid: str) -> None:
        enabled = self.cfg["enabled"]
        i = enabled.index(wid)
        menu = QMenu(self)
        menu.addAction("Move earlier", lambda: self.move_card(wid, -1)).setEnabled(i > 0)
        menu.addAction("Move later", lambda: self.move_card(wid, 1)).setEnabled(i < len(enabled) - 1)
        row_act = QAction("Start on new row", menu, checkable=True, checked=self.instances[wid].new_row)
        row_act.toggled.connect(lambda on: self.set_new_row(wid, on))
        menu.addAction(row_act)
        menu.addAction("Reset size", lambda: self.reset_size(wid))
        menu.addSeparator()
        menu.addAction("Remove", lambda: self.set_enabled(wid, False))
        menu.exec(QCursor.pos())

    def move_to(self, wid: str, index: int) -> None:
        """Place `wid` at `index` among the other visible cards (used by drag-and-drop)."""
        enabled = self.cfg["enabled"]
        visible = [i for i in enabled if i in self.registry.classes and i != wid]
        enabled.remove(wid)
        if index >= len(visible):
            enabled.insert(enabled.index(visible[-1]) + 1 if visible else len(enabled), wid)
        else:
            enabled.insert(enabled.index(visible[index]), wid)
        self.rebuild()

    def move_card(self, wid: str, delta: int) -> None:
        enabled = self.cfg["enabled"]
        i = enabled.index(wid)
        j = max(0, min(len(enabled) - 1, i + delta))
        enabled.insert(j, enabled.pop(i))
        self.rebuild()

    # --- frameless window behaviour -------------------------------------
    def toggle_max(self) -> None:
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def _edges(self, pos: QPoint) -> Qt.Edges:
        if self.isMaximized():
            return Qt.Edges()
        e = Qt.Edges()
        if pos.x() < EDGE:
            e |= Qt.LeftEdge
        if pos.x() > self.width() - EDGE:
            e |= Qt.RightEdge
        if pos.y() < EDGE:
            e |= Qt.TopEdge
        if pos.y() > self.height() - EDGE:
            e |= Qt.BottomEdge
        return e

    def _manual_resize(self, global_pos: QPoint) -> None:
        edges, start, g0 = self._resize
        d, g = global_pos - start, QRect(g0)
        mw, mh = self.minimumWidth(), self.minimumHeight()
        if edges & Qt.LeftEdge:
            g.setLeft(min(g0.left() + d.x(), g0.right() - mw + 1))
        if edges & Qt.RightEdge:
            g.setRight(max(g0.right() + d.x(), g0.left() + mw - 1))
        if edges & Qt.TopEdge:
            g.setTop(min(g0.top() + d.y(), g0.bottom() - mh + 1))
        if edges & Qt.BottomEdge:
            g.setBottom(max(g0.bottom() + d.y(), g0.top() + mh - 1))
        self.setGeometry(g)

    def mouseReleaseEvent(self, e):
        self._resize = None

    def mouseMoveEvent(self, e):
        if self._resize is not None and e.buttons() & Qt.LeftButton:
            self._manual_resize(e.globalPosition().toPoint())
            return
        edges = self._edges(e.position().toPoint())
        diag = edges in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge)
        anti = edges in (Qt.RightEdge | Qt.TopEdge, Qt.LeftEdge | Qt.BottomEdge)
        if diag:
            self.setCursor(Qt.SizeFDiagCursor)
        elif anti:
            self.setCursor(Qt.SizeBDiagCursor)
        elif edges & (Qt.LeftEdge | Qt.RightEdge):
            self.setCursor(Qt.SizeHorCursor)
        elif edges & (Qt.TopEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.unsetCursor()

    def mousePressEvent(self, e):
        edges = self._edges(e.position().toPoint())
        if e.button() == Qt.LeftButton and edges and not self.windowHandle().startSystemResize(edges):
            # No native resize on this platform: resize the window ourselves.
            self._resize = (edges, e.globalPosition().toPoint(), self.geometry())

    def save_geometry(self) -> None:
        self.cfg["maximized"] = self.isMaximized()
        if not (self.isMaximized() or self.isFullScreen() or self.isMinimized()):
            g = self.geometry()  # on Wayland the position is compositor-controlled; the size is what carries over
            self.cfg["geometry"] = [g.x(), g.y(), g.width(), g.height()]
        config.save(self.cfg)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._geom_timer.start()

    def moveEvent(self, e):
        super().moveEvent(e)
        self._geom_timer.start()

    def changeEvent(self, e):
        super().changeEvent(e)
        if e.type() == QEvent.WindowStateChange:
            self._geom_timer.start()

    def closeEvent(self, e):
        self.save_geometry()
        super().closeEvent(e)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("System Manager")
    app.setDesktopFileName("systemmanager")
    app.setStyleSheet(QSS)
    win = Dashboard()
    win.showMaximized() if win.cfg["maximized"] else win.show()
    return app.exec()
