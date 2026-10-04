"""One shared sampler. Widgets read from it; each value is computed at most once per tick."""
import shutil
import subprocess
import sys
import time

import psutil

_SKIP_FSTYPES = {"squashfs", "tmpfs", "devtmpfs", "overlay", "efivarfs", "iso9660", "devfs", "autofs"}
MAC_DATA_VOLUME = "/System/Volumes/Data"


def skip_partition(fstype: str, mountpoint: str, platform: str = sys.platform) -> bool:
    """True for pseudo and system-internal mounts that only add clutter to a disk list."""
    if fstype in _SKIP_FSTYPES:
        return True
    if platform == "darwin":
        # macOS splits one disk into many APFS volumes under /System/Volumes (VM, Preboot, Update...).
        # Keep only the user-data volume; "/" is the read-only system volume.
        if mountpoint.startswith("/System/Volumes/") and mountpoint != MAC_DATA_VOLUME:
            return True
        if mountpoint.startswith(("/private/var/vm", "/System/Volumes/Data/")):
            return True
    return False


def collapse_mac_volumes(disks: list[dict]) -> list[dict]:
    """On macOS show the Data volume as "/" (it holds the real used/free space) and hide the system volume."""
    if not any(d["mount"] == MAC_DATA_VOLUME for d in disks):
        return disks
    out = []
    for d in disks:
        if d["mount"] == "/":
            continue
        out.append({**d, "label": "/  (Macintosh HD)"} if d["mount"] == MAC_DATA_VOLUME else d)
    return out


class Stats:
    def __init__(self):
        self._cache: dict = {}
        self._net_prev = None
        self._procs: dict[int, psutil.Process] = {}
        psutil.cpu_percent(percpu=True)  # prime

    def advance(self) -> None:
        self._cache.clear()

    def _once(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def cpu_cores(self) -> list[float]:
        return self._once("cores", lambda: psutil.cpu_percent(percpu=True))

    def cpu_total(self) -> float:
        cores = self.cpu_cores()
        return sum(cores) / len(cores) if cores else 0.0

    def load_avg(self) -> tuple[float, float, float]:
        return psutil.getloadavg()

    def memory(self):
        return self._once("mem", psutil.virtual_memory)

    def swap(self):
        return self._once("swap", psutil.swap_memory)

    def disks(self) -> list[dict]:
        def collect():
            seen, out = set(), []
            for p in psutil.disk_partitions(all=False):
                if skip_partition(p.fstype, p.mountpoint) or p.device in seen:
                    continue
                seen.add(p.device)
                try:
                    u = psutil.disk_usage(p.mountpoint)
                except OSError:
                    continue
                out.append({"mount": p.mountpoint, "label": p.mountpoint, "device": p.device,
                            "fstype": p.fstype, "total": u.total, "used": u.used, "percent": u.percent})
            return collapse_mac_volumes(out) if sys.platform == "darwin" else out
        return self._once("disks", collect)

    def net_rate(self) -> tuple[float, float]:
        """(download, upload) in bytes/sec since the previous call."""
        def collect():
            now, io = time.monotonic(), psutil.net_io_counters()
            prev, self._net_prev = self._net_prev, (now, io)
            if not prev or now <= prev[0]:
                return 0.0, 0.0
            dt = now - prev[0]
            return (io.bytes_recv - prev[1].bytes_recv) / dt, (io.bytes_sent - prev[1].bytes_sent) / dt
        return self._once("net", collect)

    def systemd(self) -> dict:
        """System- and user-scope service summary: overall state, running/total counts, failed unit names."""
        def collect():
            out = {}
            if not shutil.which("systemctl"):
                return out
            for scope, flags in (("system", []), ("user", ["--user"])):
                state = _systemctl(*flags, "is-system-running")
                rows = [ln.split(None, 4) for ln in
                        _systemctl(*flags, "list-units", "--type=service", "--all", "--no-legend", "--plain").splitlines()]
                rows = [r for r in rows if len(r) >= 4]
                out[scope] = {
                    "state": state or "unavailable",
                    "total": len(rows),
                    "running": sum(r[3] == "running" for r in rows),
                    "failed": [r[0] for r in rows if r[2] == "failed"],
                }
            return out
        return self._once("systemd", collect)

    def top_procs(self, n: int = 6, key: str = "cpu") -> list[dict]:
        def collect():
            live = {}
            rows = []
            ncpu = psutil.cpu_count() or 1
            for p in psutil.process_iter():
                proc = self._procs.get(p.pid, p)
                live[p.pid] = proc
                try:
                    rows.append({"pid": p.pid, "name": proc.name(),
                                 "cpu": proc.cpu_percent(None) / ncpu,
                                 "mem": proc.memory_percent()})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            self._procs = live
            return rows
        rows = self._once("procs", collect)
        return sorted(rows, key=lambda r: r[key], reverse=True)[:n]


def _systemctl(*args: str) -> str:
    try:
        r = subprocess.run(["systemctl", *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout.strip()


def fmt_bytes(n: float, suffix: str = "") -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024 or unit == "TiB":
            return f"{n:.0f} {unit}{suffix}" if unit == "B" else f"{n:.1f} {unit}{suffix}"
        n /= 1024
