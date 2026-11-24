"""Time-lapse capture job: one run = one archived moment (or a logged skip).

Privacy: frames are only kept if the camgate gate is ok before AND after the
snapshots with the same last_not_ok_at; every frame is losslessly cropped.
"""
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Callable, NamedTuple

import numpy as np
from PIL import Image

from camgate.config import NO_CROP, SURVEIL_CONF
from camgate.config import load_crop as _load_crop

from . import conditions, config, lossless, storage


class Deps(NamedTuple):
    read_gate: Callable
    read_conditions: Callable
    read_last_mist: Callable      # -> epoch|None; raises on failure (fail closed)
    fetch_snapshot: Callable      # -> jpeg bytes; raises on failure
    light_window: Callable
    load_crop: Callable
    root: Path
    clock: Callable = time.time
    sleep: Callable = time.sleep


def sharpness(jpeg: bytes) -> float:
    """Variance of a 3x3 Laplacian on a 1/4-scale grayscale."""
    with Image.open(io.BytesIO(jpeg)) as im:
        g = im.convert("L")
        g = g.reduce(4)
    a = np.asarray(g, dtype=np.float64)
    lap = (-4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:])
    return float(lap.var())


def _skip(reason, saved=None):
    return {"saved": saved or [], "skipped": reason}


def capture_once(now: datetime, deps: Deps) -> dict:
    root = Path(deps.root)
    reason = storage.space_check(root)
    if reason:
        return _skip(reason)
    w = deps.light_window()
    if w is None:
        return _skip("light_schedule_unknown")
    ph = conditions.phase(now, w)
    crop = deps.load_crop()
    if crop is None:
        return _skip("crop_invalid")
    if crop is NO_CROP:
        return _skip("crop_none")
    t = deps.clock()
    gate = deps.read_gate()
    reason = conditions.gate_check(gate, t)
    if reason:
        return _skip(reason)
    cond = deps.read_conditions()
    try:
        last_mist = deps.read_last_mist()
    except Exception:
        return _skip("mist_unknown")
    reason = conditions.mist_check(cond, last_mist, t)
    if reason:
        return _skip(reason)

    n = config.BURST_N if ph == "plateau" else 1
    shots = []
    try:
        for i in range(n):
            if i:
                deps.sleep(config.BURST_GAP_S)
            shots.append(deps.fetch_snapshot())
    except Exception:
        return _skip("camera_error")

    snap_ts = deps.clock()
    deps.sleep(config.GATE_SETTLE_S)   # let a door opened just before the snapshot surface
    gate2 = deps.read_gate()
    reason = conditions.gate_check(gate2, deps.clock())
    if reason:
        return _skip(reason)
    if gate2.get("last_not_ok_at") != gate.get("last_not_ok_at"):
        return _skip("gate_changed")
    gn = gate2.get("now")
    if not isinstance(gn, (int, float)) or isinstance(gn, bool) or \
            not gn >= snap_ts + config.GATE_SETTLE_S:
        return _skip("gate_unsettled")

    try:
        with Image.open(io.BytesIO(shots[0])) as im:
            frame = im.size
        mcu = lossless.mcu_size(shots[0])
        snapped = lossless.snap_inward(crop, mcu, frame)
    except Exception:
        snapped = None
        frame = mcu = None
    if snapped is None:
        return _skip("crop_invalid")
    try:
        for s in shots[1:]:
            with Image.open(io.BytesIO(s)) as im:
                size = im.size
            if size != frame or lossless.mcu_size(s) != mcu:
                return _skip("frame_mismatch")
    except Exception:
        return _skip("frame_mismatch")
    try:
        outs = [lossless.crop_rotate(s, snapped) for s in shots]
        sharp = [sharpness(o) for o in outs]
    except Exception:
        return _skip("lossless_error")

    paths = [storage.frame_path(root, now, None if n == 1 else i) for i in range(n)]
    created = []
    try:
        for p, o in zip(paths, outs):
            storage.write_new(p, o)
            created.append(p)
        storage.append_sidecar(paths[0].parent, {
            "time": now.astimezone().isoformat(timespec="seconds"),
            "files": [str(p.relative_to(root)) for p in paths],
            "phase": ph,
            "geometry": lossless.archive_geometry(snapped),
            "sharpness": sharp,
        })
    except Exception as e:
        for p in created:      # only what this run created; never an earlier frame
            try:
                p.unlink()
            except OSError:
                pass
        return _skip("frame_exists" if isinstance(e, FileExistsError) else "write_error")
    return {"saved": [str(p) for p in paths], "skipped": None}


# ---- real dependencies (loopback only) ----

def _http_get(url: str, timeout: float = 5) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def _json_or_none(url):
    try:
        return json.loads(_http_get(url))
    except Exception:
        return None


def read_last_mist_influx() -> "float|None":
    q = "SELECT last(value) FROM mist_event WHERE time > now() - 10m"
    url = config.INFLUX_URL + "?" + urllib.parse.urlencode(
        {"db": config.INFLUX_DB, "q": q, "epoch": "s"})
    data = json.loads(_http_get(url))
    res = data["results"][0]
    if "error" in res:
        raise RuntimeError(res["error"])
    series = res.get("series")
    if not series:
        return None
    return float(series[0]["values"][0][0])


def real_deps() -> Deps:
    return Deps(
        read_gate=lambda: _json_or_none(config.GATE_URL),
        read_conditions=lambda: _json_or_none(config.CONDITIONS_URL),
        read_last_mist=read_last_mist_influx,
        fetch_snapshot=lambda: _http_get(config.SNAPSHOT_URL),
        light_window=conditions.light_window,
        load_crop=lambda: _load_crop(SURVEIL_CONF),
        root=Path(config.ARCHIVE_ROOT),
    )


def main() -> int:
    now = datetime.now()
    line = None
    try:
        root = Path(config.ARCHIVE_ROOT)
        if not root.is_dir():
            print("%s capture: archive root missing" % now.isoformat(timespec="seconds"),
                  file=sys.stderr)
            return 0
        r = capture_once(now, real_deps())
        line = "%s saved=%d skipped=%s" % (now.isoformat(timespec="seconds"),
                                           len(r["saved"]), r["skipped"])
    except Exception as e:
        line = "%s error=%r" % (now.isoformat(timespec="seconds"), e)
    try:
        log = Path(config.ARCHIVE_ROOT) / "logs" / "capture.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a") as f:
            f.write(line + "\n")
    except Exception:
        print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
