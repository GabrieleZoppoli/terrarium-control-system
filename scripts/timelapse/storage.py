"""Archive layout, atomic writes, day sidecars and space limits."""
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import config

_GB = 1024 ** 3


def frame_path(root, ts_local: datetime, idx: Optional[int]) -> Path:
    name = ts_local.strftime("%H%M") + ("" if idx is None else "-%d" % idx) + ".jpg"
    return Path(root) / "frames" / ts_local.strftime("%Y/%m/%d") / name


def write_atomic(path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_sidecar(day_dir, entry: dict) -> None:
    day_dir = Path(day_dir)
    p = day_dir / "day.json"
    frames = []
    try:
        loaded = json.loads(p.read_text())
        if isinstance(loaded, dict) and isinstance(loaded.get("frames"), list):
            frames = loaded["frames"]
    except (OSError, ValueError):
        pass
    frames.append(entry)
    write_atomic(p, json.dumps({"frames": frames}, indent=1).encode())


def _tree_bytes(root: Path) -> int:
    total = 0
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return total


def space_check(root, cap_gb=config.CAP_GB, floor_gb=config.FLOOR_GB) -> Optional[str]:
    try:
        free = shutil.disk_usage(str(root)).free
        if free < floor_gb * _GB:
            return "disk_low"
        if _tree_bytes(Path(root)) >= cap_gb * _GB:
            return "archive_full"
    except OSError:
        return "disk_low"
    return None
