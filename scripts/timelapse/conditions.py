"""Pure capture-condition decisions (light phase, camgate gate, misting).

All checks fail closed: anything malformed yields a reason string.
I/O helpers (fetching the gate, querying InfluxDB) live in capture.py.
"""
import json
import math
import os
import time
from datetime import datetime
from typing import NamedTuple, Optional

from timelapse import config


class LightWindow(NamedTuple):
    on: float
    off: float
    plateau_start: float
    plateau_end: float


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def light_window(globals_path: str = config.NR_GLOBALS) -> Optional[LightWindow]:
    try:
        if time.time() - os.stat(globals_path).st_mtime > config.GLOBALS_MAX_AGE_S:
            return None
        with open(globals_path) as f:
            data = json.load(f)
        pl = data["payload"]
        vals = [pl[k] for k in ("photo_light_on", "photo_light_off",
                                "photo_midday_up", "photo_midday_down")]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not all(_num(v) for v in vals):
        return None
    on, off, up, down = vals
    w = LightWindow(on, off, up + 30, down)
    if not (w.on < w.plateau_start < w.plateau_end < w.off):
        return None
    return w


def phase(now_local: datetime, w: LightWindow) -> str:
    m = now_local.hour * 60 + now_local.minute
    if w.plateau_start <= m < w.plateau_end:
        return "plateau"
    if w.on <= m < w.off:
        return "lit"
    return "night"


def gate_check(gate: Optional[dict], now: float) -> Optional[str]:
    if gate is None:
        return "gate_unreachable"
    if not isinstance(gate, dict) or not _num(now):
        return "gate_invalid"
    ok = gate.get("ok")
    if not isinstance(ok, bool):
        return "gate_invalid"
    if not ok:
        reason = gate.get("reason")
        if isinstance(reason, str) and reason:
            return "gate_" + reason
        return "gate_invalid"
    last = gate.get("last_not_ok_at")
    if not _num(last) or last > now:
        return "gate_invalid"
    if now - last < config.AFTER_PRIVATE_S:
        return "after_private"
    return None


def mist_check(conditions: Optional[dict], last_mist_ts: Optional[float],
               now: float) -> Optional[str]:
    if conditions is None:
        return "conditions_unreachable"
    if not isinstance(conditions, dict) or not isinstance(conditions.get("mister"), bool):
        return "conditions_invalid"
    if conditions["mister"]:
        return "misting"
    if last_mist_ts is None:
        return None
    if not _num(last_mist_ts) or not _num(now):
        return "conditions_invalid"
    if now - last_mist_ts < config.MIST_QUIET_S:
        return "mist_recent"
    return None
