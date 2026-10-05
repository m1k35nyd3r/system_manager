import shutil
import sys

from PySide6.QtWidgets import QLabel, QVBoxLayout

from ..api import Bar, DashboardWidget, level_color


class BluetoothWidget(DashboardWidget):
    id = "bluetooth"
    title = "Bluetooth batteries"
    interval = 30
    supported = sys.platform.startswith("linux") and shutil.which("bluetoothctl") is not None \
        and shutil.which("upower") is not None

    def setup(self, layout):
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(12)
        layout.addLayout(self.rows_layout)
        self.empty = QLabel("No connected Bluetooth devices")
        self.empty.setObjectName("muted")
        layout.addWidget(self.empty)
        self.rows: dict[str, tuple[QLabel, QLabel, Bar]] = {}

    def update_data(self, stats):
        devices = stats.bluetooth()
        wanted = {d["address"] for d in devices}
        for addr in set(self.rows) - wanted:
            name, detail, bar = self.rows.pop(addr)
            for w in (name, detail, bar):
                w.deleteLater()
        self.empty.setVisible(not devices)
        for d in devices:
            if d["address"] not in self.rows:
                name, detail, bar = QLabel(), QLabel(), Bar(8, low_is_bad=True)
                detail.setObjectName("muted")
                box = QVBoxLayout()
                box.setSpacing(3)
                for w in (name, bar, detail):
                    box.addWidget(w)
                self.rows_layout.addLayout(box)
                self.rows[d["address"]] = (name, detail, bar)
            name, detail, bar = self.rows[d["address"]]
            name.setText(d["name"])
            pct = d["percent"]
            bar.setVisible(pct is not None)
            if pct is None:
                detail.setText("⚡ Charging, level not reported" if d["charging"] else "Battery not reported")
                continue
            bar.set_value(pct)
            color = level_color(100 - pct).name()
            charging = "  ⚡ charging" if d["charging"] else ""
            detail.setText(f"<span style='color:{color}'>{pct:.0f}%</span>{charging}")
