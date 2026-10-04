"""Example plugin. Copy into ~/.config/systemmanager/widgets/ and it appears under "+ Widgets" instantly."""
import time

import psutil
from PySide6.QtWidgets import QLabel

from systemmanager.api import DashboardWidget


class UptimeWidget(DashboardWidget):
    id = "uptime"
    title = "Uptime"
    interval = 5

    def setup(self, layout):
        self.label = QLabel()
        self.label.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(self.label)

    def update_data(self, stats):
        s = int(time.time() - psutil.boot_time())
        d, s = divmod(s, 86400)
        h, s = divmod(s, 3600)
        self.label.setText(f"{d}d {h}h {s // 60}m")
