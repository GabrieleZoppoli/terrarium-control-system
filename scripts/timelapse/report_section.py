"""Flowers section for terrarium-report.py. Pure, read-only, never raises."""
import json
import os
from collections import Counter
from datetime import timedelta
from pathlib import Path

MAX_AGE_S = 36 * 3600
NEEDS_YOU = "Some flowers need you: reply in chat with corrections"
_LOG_TAIL = 2 * 1024 * 1024


def _latest_status(root: Path, now):
    best = None
    for p in (root / "status").glob("vision-*.json"):
        try:
            mt = p.stat().st_mtime
        except OSError:
            continue
        if best is None or mt > best[0]:
            best = (mt, p)
    if best is None or now.timestamp() - best[0] > MAX_AGE_S:
        return None
    return best[1]


def _total_gb(root: Path) -> float:
    total = 0
    for dp, _dn, fn in os.walk(root / "frames"):
        for f in fn:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return total / 1024 ** 3


def _archive_line(root: Path, now) -> str:
    y = (now - timedelta(days=1)).date()
    n = 0
    try:
        day = root / "frames" / y.strftime("%Y/%m/%d") / "day.json"
        n = len(json.loads(day.read_text()).get("frames", []))
    except (OSError, ValueError, AttributeError):
        pass
    skips = Counter()
    try:
        with open(root / "logs" / "capture.log", "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - _LOG_TAIL))
            data = f.read().decode("utf-8", "replace")
        ys = y.isoformat()
        for ln in data.splitlines():
            if not ln.startswith(ys) or " skipped=" not in ln:
                continue
            r = ln.split(" skipped=", 1)[1].strip()
            if r and r != "None":
                skips[r] += 1
    except OSError:
        pass
    sk = ", ".join("%s: %d" % kv for kv in sorted(skips.items())) or "none"
    return "archive: %d frames yesterday, %.1f GB total, skipped: {%s}" % (
        n, _total_gb(root), sk)


def timelapse_section(root, now) -> dict:
    """Return {"lines": [...], "checkin": path|None}; empty lines = no section."""
    try:
        root = Path(root)
        if not root.is_dir():
            return {"lines": [], "checkin": None}
        lines = ["FLOWERS"]
        checkin = None
        sp = _latest_status(root, now)
        if sp is None:
            lines.append("  no vision run yet")
        else:
            st = json.loads(sp.read_text())
            status = str(st.get("status", "unknown"))
            if status == "ok":
                for s in st.get("summary") or []:
                    lines.append("  " + str(s))
                if not st.get("summary"):
                    lines.append("  no changes")
            else:
                lines.append("  vision %s: %s" % (status, st.get("why", "")))
            if status == "ok" and st.get("pending"):
                ds = sp.stem[len("vision-"):]
                cp = root / "status" / ("checkin-%s.jpg" % ds)
                if cp.is_file():
                    checkin = str(cp)
                    lines.append("  " + NEEDS_YOU)
        try:
            lines.append("  " + _archive_line(root, now))
        except Exception:
            pass
        return {"lines": lines, "checkin": checkin}
    except Exception:
        return {"lines": [], "checkin": None}
