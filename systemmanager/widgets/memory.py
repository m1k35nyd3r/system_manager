from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from ..api import Bar, DashboardWidget, Gauge, Sparkline, fmt_bytes


class MemoryWidget(DashboardWidget):
    id = "memory"
    title = "Memory"

    def setup(self, layout):
        row = QHBoxLayout()
        self.gauge = Gauge(130)
        row.addWidget(self.gauge)
        col = QVBoxLayout()
        self.spark = Sparkline(color="#b57bee")
        self.ram_label = QLabel()
        self.ram_label.setObjectName("muted")
        col.addWidget(self.spark)
        col.addWidget(self.ram_label)
        row.addLayout(col, 1)
        layout.addLayout(row)
        self.swap_label = QLabel()
        self.swap_label.setObjectName("muted")
        self.swap_bar = Bar(6)
        layout.addWidget(self.swap_label)
        layout.addWidget(self.swap_bar)

    def update_data(self, stats):
        m, s = stats.memory(), stats.swap()
        self.gauge.set_value(m.percent, "RAM")
        self.spark.push(m.percent)
        self.ram_label.setText(f"{fmt_bytes(m.used)} used of {fmt_bytes(m.total)}\n{fmt_bytes(m.available)} available")
        if s.total:
            self.swap_label.setText(f"Swap  {fmt_bytes(s.used)} / {fmt_bytes(s.total)}")
            self.swap_bar.set_value(s.percent)
        else:
            self.swap_label.setText("Swap  none")
            self.swap_bar.set_value(0)
