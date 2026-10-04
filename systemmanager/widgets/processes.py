from PySide6.QtWidgets import QGridLayout, QLabel, QWidget
from PySide6.QtCore import Qt

from ..api import DashboardWidget

ROWS = 6


class ProcessesWidget(DashboardWidget):
    id = "processes"
    title = "Top processes"
    interval = 2
    span = 2

    def setup(self, layout):
        box = QWidget()
        grid = QGridLayout(box)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setColumnStretch(1, 1)
        for c, h in enumerate(("PID", "Name", "CPU", "Mem")):
            lbl = QLabel(h)
            lbl.setObjectName("muted")
            grid.addWidget(lbl, 0, c, Qt.AlignRight if c in (2, 3) else Qt.AlignLeft)
        self.cells = []
        for r in range(1, ROWS + 1):
            row = [QLabel() for _ in range(4)]
            for c, lbl in enumerate(row):
                grid.addWidget(lbl, r, c, Qt.AlignRight if c in (2, 3) else Qt.AlignLeft)
            self.cells.append(row)
        layout.addWidget(box)

    def update_data(self, stats):
        procs = stats.top_procs(ROWS)
        for row, p in zip(self.cells, procs + [None] * ROWS):
            vals = ("", "", "", "") if p is None else (str(p["pid"]), p["name"], f"{p['cpu']:.1f}%", f"{p['mem']:.1f}%")
            for lbl, v in zip(row, vals):
                lbl.setText(v)
