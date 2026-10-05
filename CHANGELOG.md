# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Bluetooth widget: battery level of every connected Bluetooth device (Linux; needs `bluetoothctl` and `upower`). Off by default.
- `Stats.bluetooth()` and a `low_is_bad` option on `Bar` for charge-style levels.

## [0.6.0] - 2026-10-04

### Added
- macOS support (written for macOS; verified on Linux with simulated Mac data, not yet on a real Mac).
- `install.sh` builds `~/Applications/System Manager.app` and a launchd login agent on macOS; `tools/make_icns.py` generates the app icon.
- Widgets can set `supported = False` to stay out of the **+ Widgets** menu on platforms they don't suit.
- Fallback window move and resize for platforms without native compositor requests.

### Changed
- Disk widget hides macOS system-internal APFS volumes and shows the Data volume as `/ (Macintosh HD)`; also skips `devfs` and `autofs` mounts.
- Systemd widget is only offered when `systemctl` is available (Linux).
- Config folder on macOS is `~/Library/Application Support/SystemManager`. The Linux location is unchanged.

### Fixed
- Dashboard's card-reorder method no longer shadows Qt's `QWidget.move` (renamed to `move_card`), which broke dragging the window by the title bar.

## [0.5.0] - 2026-10-04

### Changed
- The window's current size is now the next start-up size. It is saved about half a second after you stop resizing, so it survives a crash, logout or kill, not only a clean close.
- The maximized state is remembered and restored.

## [0.4.0] - 2026-10-04

### Added
- **Start on new row** in a card's right-click menu: the card drops to its own row and stays there instead of flowing back up beside the previous card. Saved per widget.

## [0.3.1] - 2026-10-04

### Fixed
- Narrow windows now stack widgets in a single column instead of clipping the right-hand side. The column count is based on the visible area and on the widest card's minimum width.
- Cards no longer stay squeezed after the window is made smaller and then larger again (stale grid column stretch).

### Changed
- Minimum window width raised from 420 to 440 px so a single column always fits.

## [0.3.0] - 2026-10-04

### Added
- Resizable widgets: drag the grip in a card's bottom-right corner. Width snaps to grid columns, height is free (never smaller than the content needs). Sizes are saved per widget.
- **Reset size** in the card's right-click menu.

## [0.2.0] - 2026-10-04

### Added
- Systemd services widget: system and user scope state, running/loaded counts and failed units (opt-in via **+ Widgets**).
- Drag-to-reorder: drag a card by its heading and drop it where you want it; a blue marker shows the drop position.
- `install.sh` to install the desktop launcher and login autostart (`--no-autostart`, `--uninstall` supported).
- Application icon (`assets/systemmanager.svg`).
- README.

## [0.1.0] - 2026-10-04

### Added
- Frameless dashboard window (PySide6) with custom title bar, edge resizing and native move/resize on Wayland.
- Built-in widgets: CPU (overall, per-core, load average), memory and swap, disk space per mount, network throughput, top processes.
- Plugin system: drop a `.py` file into `~/.config/systemmanager/widgets/` to add a widget; hot-reloaded without a restart, and broken plugins are isolated and reported in the title bar.
- Responsive card grid, show/hide widgets from the **+ Widgets** menu, right-click to move or remove cards.
- Layout, enabled widgets and window geometry persisted to `~/.config/systemmanager/config.json`.
- Example plugin in `examples/uptime.py`.
