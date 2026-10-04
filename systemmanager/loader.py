"""Discovers widget classes from built-ins and the user folder, and hot-reloads the latter."""
import importlib.util
import inspect
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal

from . import config
from .api import DashboardWidget

log = logging.getLogger("systemmanager")
BUILTIN_DIR = Path(__file__).parent / "widgets"


def _load_file(path: Path, prefix: str) -> list[type]:
    if path.parent == BUILTIN_DIR:  # real package members, so relative imports work
        name = f"systemmanager.widgets.{path.stem}"
        mod = importlib.import_module(name)
    else:
        name = f"{prefix}.{path.stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return [c for _, c in inspect.getmembers(mod, inspect.isclass)
            if issubclass(c, DashboardWidget) and c is not DashboardWidget and c.__module__ == name and c.id and c.supported]


class Registry(QObject):
    changed = Signal()  # emitted after a user file was (re)loaded or removed

    def __init__(self):
        super().__init__()
        self.classes: dict[str, type] = {}
        self._by_file: dict[Path, list[str]] = {}
        self.errors: dict[Path, str] = {}
        for path in sorted(BUILTIN_DIR.glob("[!_]*.py")):
            self._load(path, "systemmanager_builtin")
        config.USER_WIDGETS_DIR.mkdir(parents=True, exist_ok=True)
        for path in sorted(config.USER_WIDGETS_DIR.glob("[!_]*.py")):
            self._load(path, "systemmanager_user")

        self._watcher = QFileSystemWatcher([str(config.USER_WIDGETS_DIR)])
        self._debounce = QTimer(singleShot=True, interval=300)
        self._debounce.timeout.connect(self._rescan)
        self._watcher.directoryChanged.connect(self._debounce.start)
        self._watcher.fileChanged.connect(self._debounce.start)
        self._mtimes: dict[Path, float] = {}
        self._watch_files()

    def _load(self, path: Path, prefix: str) -> None:
        for wid in self._by_file.pop(path, []):
            self.classes.pop(wid, None)
        try:
            found = _load_file(path, prefix)
            self.errors.pop(path, None)
        except Exception as e:  # a broken plugin must never take the dashboard down
            log.exception("failed to load %s", path)
            self.errors[path] = f"{type(e).__name__}: {e}"
            return
        for cls in found:
            self.classes[cls.id] = cls
        self._by_file[path] = [c.id for c in found]

    def _watch_files(self) -> None:
        files = sorted(config.USER_WIDGETS_DIR.glob("[!_]*.py"))
        known = set(self._watcher.files())
        self._watcher.addPaths([str(f) for f in files if str(f) not in known])
        for f in files:
            self._mtimes[f] = f.stat().st_mtime

    def _rescan(self) -> None:
        current = set(config.USER_WIDGETS_DIR.glob("[!_]*.py"))
        for gone in set(self._by_file) - current - {p for p in self._by_file if p.parent == BUILTIN_DIR}:
            for wid in self._by_file.pop(gone):
                self.classes.pop(wid, None)
            self.errors.pop(gone, None)
        for path in sorted(current):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if self._mtimes.get(path) != mtime or path not in self._by_file and path not in self.errors:
                self._load(path, "systemmanager_user")
        self._watch_files()
        self.changed.emit()
