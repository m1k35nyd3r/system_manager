from PySide6.QtWidgets import QLabel, QVBoxLayout

from ..api import Bar, DashboardWidget, fmt_bytes


class DisksWidget(DashboardWidget):
    id = "disks"
    title = "Disk space"
    interval = 10

    def setup(self, layout):
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(12)
        layout.addLayout(self.rows_layout)
        layout.addStretch(1)
        self.rows: dict[str, tuple[QLabel, QLabel, Bar]] = {}

    def update_data(self, stats):
        disks = stats.disks()
        wanted = {d["mount"] for d in disks}
        for mount in set(self.rows) - wanted:
            for w in self.rows.pop(mount):
                w.deleteLater()
        for d in disks:
            if d["mount"] not in self.rows:
                name, usage, bar = QLabel(), QLabel(), Bar(8)
                usage.setObjectName("muted")
                box = QVBoxLayout()
                box.setSpacing(3)
                box.addWidget(name)
                box.addWidget(bar)
                box.addWidget(usage)
                self.rows_layout.addLayout(box)
                self.rows[d["mount"]] = (name, usage, bar)
            name, usage, bar = self.rows[d["mount"]]
            name.setText(f"{d['label']}  <span style='color:#8b93a5'>{d['device']} · {d['fstype']}</span>")
            usage.setText(f"{fmt_bytes(d['used'])} of {fmt_bytes(d['total'])}  ·  {d['percent']:.0f}% used  ·  "
                          f"{fmt_bytes(d['total'] - d['used'])} free")
            bar.set_value(d["percent"])
