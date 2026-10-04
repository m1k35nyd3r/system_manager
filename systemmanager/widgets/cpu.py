from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..api import Bar, DashboardWidget, Gauge, Sparkline


class CpuWidget(DashboardWidget):
    id = "cpu"
    title = "CPU"
    span = 2

    def setup(self, layout):
        top = QHBoxLayout()
        self.gauge = Gauge(130)
        top.addWidget(self.gauge)
        self.spark = Sparkline()
        self.load = QLabel()
        self.load.setObjectName("muted")
        col = QVBoxLayout()
        col.addWidget(self.spark)
        col.addWidget(self.load)
        top.addLayout(col, 1)
        layout.addLayout(top)

        self.cores_box = QWidget()
        self.grid = QGridLayout(self.cores_box)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(4)
        self.bars: list[Bar] = []
        layout.addWidget(self.cores_box)

    def update_data(self, stats):
        cores = stats.cpu_cores()
        total = stats.cpu_total()
        self.gauge.set_value(total, f"{len(cores)} threads")
        self.spark.push(total)
        l1, l5, l15 = stats.load_avg()
        self.load.setText(f"Load average  {l1:.2f}  {l5:.2f}  {l15:.2f}")
        if len(self.bars) != len(cores):
            for b in self.bars:
                b.deleteLater()
            self.bars = []
            for i in range(len(cores)):
                bar = Bar(6)
                self.bars.append(bar)
                self.grid.addWidget(bar, i // 4, i % 4)
        for bar, v in zip(self.bars, cores):
            bar.set_value(v)
