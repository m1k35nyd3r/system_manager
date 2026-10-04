import copy
import json
import os
import sys
from pathlib import Path


def _default_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "SystemManager"
    return Path.home() / ".config" / "systemmanager"


CONFIG_DIR = Path(os.environ.get("SYSTEMMANAGER_CONFIG_DIR") or _default_dir())
CONFIG_FILE = CONFIG_DIR / "config.json"
USER_WIDGETS_DIR = CONFIG_DIR / "widgets"

DEFAULTS = {
    "enabled": ["cpu", "memory", "disks", "network", "processes"],
    "sizes": {},
    "new_row": [],
    "maximized": False,
    "geometry": [100, 100, 1000, 640],
}


def load() -> dict:
    try:
        data = json.loads(CONFIG_FILE.read_text())
    except (OSError, ValueError):
        data = {}
    return {**copy.deepcopy(DEFAULTS), **data}


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2))
    tmp.replace(CONFIG_FILE)
