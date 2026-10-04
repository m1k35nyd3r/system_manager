import shutil
import sys

from PySide6.QtWidgets import QLabel

from ..api import DashboardWidget

MAX_FAILED = 5
STATE_COLOR = {"running": "#4cc38a", "degraded": "#ef5350", "unavailable": "#8b93a5"}


class SystemdWidget(DashboardWidget):
    id = "systemd"
    title = "Systemd services"
    interval = 10
    supported = sys.platform.startswith("linux") and shutil.which("systemctl") is not None

    def setup(self, layout):
        self.labels = {}
        for scope in ("system", "user"):
            head, detail = QLabel(), QLabel()
            detail.setObjectName("muted")
            layout.addWidget(head)
            layout.addWidget(detail)
            self.labels[scope] = (head, detail)
        layout.addStretch(1)

    def update_data(self, stats):
        for scope, info in stats.systemd().items():
            head, detail = self.labels[scope]
            color = STATE_COLOR.get(info["state"], "#f0b429")
            head.setText(f"<b>{scope.capitalize()}</b>  <span style='color:{color}'>● {info['state']}</span>"
                         f"  <span style='color:#8b93a5'>{info['running']} running / {info['total']} loaded</span>")
            failed = info["failed"]
            if failed:
                extra = f"\n+{len(failed) - MAX_FAILED} more" if len(failed) > MAX_FAILED else ""
                detail.setText("Failed: " + "\nFailed: ".join(failed[:MAX_FAILED]) + extra)
                detail.setStyleSheet("color: #ef5350;")
            else:
                detail.setText("No failed units")
                detail.setStyleSheet("")
