from PySide6.QtWidgets import QLabel

from ..api import DashboardWidget, Sparkline, fmt_bytes


class NetworkWidget(DashboardWidget):
    id = "network"
    title = "Network"

    def setup(self, layout):
        self.down_label, self.up_label = QLabel(), QLabel()
        self.down = Sparkline(auto_scale=True, color="#4cc38a")
        self.up = Sparkline(auto_scale=True, color="#f0b429")
        for w in (self.down_label, self.down, self.up_label, self.up):
            layout.addWidget(w)

    def update_data(self, stats):
        rx, tx = stats.net_rate()
        self.down_label.setText(f"↓ Download  <b>{fmt_bytes(rx, '/s')}</b>")
        self.up_label.setText(f"↑ Upload  <b>{fmt_bytes(tx, '/s')}</b>")
        self.down.push(rx)
        self.up.push(tx)
