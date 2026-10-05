# System Manager

A frameless desktop dashboard for Linux and macOS for disk space, CPU, memory, network, processes and systemd services, with widgets you can add at any time. Built with Python, PySide6 (Qt 6) and psutil.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh
```

To add it to your application menu and start it at login:

```bash
./install.sh                  # launcher + autostart
./install.sh --no-autostart   # launcher only
./install.sh --uninstall      # remove both
```

On Linux this writes `.desktop` files. On macOS it builds `~/Applications/System Manager.app` (so it appears in Launchpad and Spotlight) and a launchd login agent, which takes effect at your next login.

## Platforms

| | Linux | macOS |
| --- | --- | --- |
| Dashboard, widgets, plugins | ✅ tested | ✅ expected to work; **not yet tested on a real Mac** |
| Disk widget | all real mounts | system APFS volumes are hidden; the Data volume is shown as `/ (Macintosh HD)` |
| Systemd widget | ✅ (needs `systemctl`) | not offered, since macOS has no systemd |
| Window move / resize | native compositor request | native request if Qt supports it, otherwise a built-in drag fallback |
| Installer | `.desktop` + autostart entry | `.app` bundle + launchd agent |

Windows is not supported.

A widget can opt out of platforms it doesn't support by setting `supported = False` on its class.

## Using it

| Action | How |
| --- | --- |
| Move the window | Drag the title bar |
| Resize | Drag any edge or corner |
| Maximize | Double-click the title bar |
| Show / hide widgets | **+ Widgets** menu |
| Reorder | Drag a card by its heading |
| Resize a card | Drag the grip in its bottom-right corner (width snaps to columns) |
| Pin a card to its own row | Right-click it → **Start on new row** |
| Move / remove / reset size | Right-click a card |

The grid adapts to the window width: wide windows show several columns, and narrow ones stack the cards in a single column.

Built-in widgets: `cpu`, `memory`, `disks`, `network`, `processes`, `systemd` and `bluetooth` (both off by default; Linux only, need `systemctl` / `bluetoothctl` + `upower`).

The window size (and maximized state) is saved as you resize, and used the next time it starts. On Wayland the compositor decides where a window appears, so only the size carries over.

Settings are stored in `~/.config/systemmanager/config.json` (on macOS, `~/Library/Application Support/SystemManager/config.json`) (enabled widgets and their order, card sizes, pinned rows, window size and maximized state). Set `SYSTEMMANAGER_CONFIG_DIR` to use a different folder.

## Writing a widget

Drop a `.py` file into the `widgets` folder next to the config file (`~/.config/systemmanager/widgets/` on Linux) (**+ Widgets → Open widgets folder**). It is loaded immediately and reloaded whenever you save it. See [examples/uptime.py](examples/uptime.py).

```python
from PySide6.QtWidgets import QLabel
from systemmanager.api import DashboardWidget

class HelloWidget(DashboardWidget):
    id = "hello"         # unique key
    title = "Hello"      # card heading
    interval = 5         # seconds between updates
    span = 1             # default grid columns used (users can resize)
    supported = True     # False hides the widget (e.g. on an unsupported OS)

    def setup(self, layout):
        self.label = QLabel()
        layout.addWidget(self.label)

    def update_data(self, stats):
        self.label.setText(f"CPU {stats.cpu_total():.0f}%")
```

`systemmanager.api` also exports `Gauge`, `Bar`, `Sparkline`, `level_color` and `fmt_bytes` for drawing. The `stats` object is a shared sampler (`cpu_cores()`, `cpu_total()`, `memory()`, `swap()`, `disks()`, `net_rate()`, `top_procs()`, `systemd()`, `bluetooth()`); each value is computed at most once per second no matter how many widgets read it. A plugin that fails to load or raises in `update_data` is reported in the title bar and the log, and never takes the dashboard down.

## Notes

- Windows are moved and resized with the compositor's native requests, so it works on Wayland and X11 (and falls back to manual dragging where a platform lacks them). GNOME on Wayland does not let normal windows sit on the desktop layer, so this is a regular (frameless) window.
- Layout: `systemmanager/app.py` (window, grid, drag and drop), `loader.py` (plugin discovery and hot reload), `stats.py` (sampler), `gauges.py` (custom painting), `widgets/` (built-ins), `install.sh` and `tools/` (launchers and icon generation).

See [CHANGELOG.md](CHANGELOG.md) for release notes.
