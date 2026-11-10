#!/usr/bin/env python3
"""
terrarium-report.py: structured, baseline-aware status report.

Replaces the 07:00 / 21:00 sitrep emails (terrarium-sitrep.py --email).

What makes it different from the sitrep:
  * Every number is compared with the SAME HOURS on each of the previous
    7 days, so "unusual" means unusual for this terrarium at this time of day
    (robust z-score on median/MAD, plus a minimum meaningful change).
  * Findings are ranked (red / yellow / info). The email subject and the
    "Needs attention" box show only what needs a look; everything else is
    in the tables below.
  * It explains likely causes where it can (e.g. freezer working harder
    because the room was warmer), predicts when the water tank needs a
    refill, and spots freezer short-cycling, data gaps and disk growth.
  * Alert episodes from terrarium-health.py are grouped with start, end and
    duration instead of a count of emoji lines.
  * Each run saves a JSON snapshot, so the next report can say what is new
    and what has cleared since last time.

Usage:
  terrarium-report.py                         text report, last 24 h
  terrarium-report.py --format html > r.html  HTML preview
  terrarium-report.py --format json           machine-readable
  terrarium-report.py --email                 send + save snapshot (07:00)
  terrarium-report.py --email --hours 12 --quiet-if-green   (21:00)

Credentials come from /etc/terrarium/secrets.env (see
scripts/terrarium-secrets.env.example). Install notes: docs/reporting.md.
"""

import argparse
import glob
import html
import json
import os
import re
import shutil
import smtplib
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Rome")
except Exception:  # pragma: no cover - very old Python
    TZ = timezone(timedelta(hours=1))


# ── Config ──────────────────────────────────────────────────────────────

SECRETS_FILES = [
    os.environ.get("TERRARIUM_SECRETS", ""),
    "/etc/terrarium/secrets.env",
    os.path.expanduser("~/.config/terrarium/secrets.env"),
]


def load_secrets():
    """Read KEY=VALUE lines into os.environ (existing env wins)."""
    for path in SECRETS_FILES:
        if path and os.path.isfile(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            return path
    return None


load_secrets()


def env(key, default):
    v = os.environ.get(key)
    if v is None or v == "":
        return default
    try:
        return type(default)(v)
    except (TypeError, ValueError):
        return default


INFLUX_URL    = env("TERRARIUM_INFLUX_URL", "http://localhost:8086")
INFLUX_DB     = env("TERRARIUM_INFLUX_DB", "highland")
LEDGER_FILE   = env("TERRARIUM_LEDGER", "/home/pi/.terrarium-health-ledger.jsonl")
SNAP_DIR      = env("TERRARIUM_REPORT_DIR", "/home/pi/terrarium-reports")
SNAP_KEEP_DAYS = env("TERRARIUM_REPORT_KEEP_DAYS", 90)
BASELINE_DAYS = env("TERRARIUM_BASELINE_DAYS", 7)
KWH_PRICE     = env("TERRARIUM_KWH_PRICE", 0.30)   # EUR/kWh

# Thresholds. Every one can be overridden from secrets.env.
TEMP_HIGH      = env("TERRARIUM_TEMP_HIGH", 25.0)   # window max above this → yellow
TEMP_LOW       = env("TERRARIUM_TEMP_LOW", 10.0)
HUMI_LOW       = env("TERRARIUM_HUMI_LOW", 65.0)    # window min below this → yellow
TEMP_BAND      = env("TERRARIUM_TEMP_BAND", 1.0)    # ±°C around target = "in band"
HUMI_BAND      = env("TERRARIUM_HUMI_BAND", 5.0)    # ±pp around target
WATER_WARN     = env("TERRARIUM_WATER_WARN", 15.0)  # % usable
WATER_RED      = env("TERRARIUM_WATER_RED", 5.0)
WATER_ETA_WARN_DAYS = env("TERRARIUM_WATER_ETA_WARN_DAYS", 2.0)
SHORT_CYCLE_MIN = env("TERRARIUM_SHORT_CYCLE_MIN", 5)  # freezer ON run shorter than this
SHORT_CYCLE_WARN = env("TERRARIUM_SHORT_CYCLE_WARN", 3)
GAP_WARN_MIN   = env("TERRARIUM_GAP_WARN_MIN", 30)
DISK_WARN_PCT  = env("TERRARIUM_DISK_WARN_PCT", 85.0)
CPU_TEMP_WARN  = env("TERRARIUM_CPU_TEMP_WARN", 75.0)
Z_WARN         = env("TERRARIUM_Z_WARN", 3.0)        # robust z for "unusual"
Z_NOTE         = env("TERRARIUM_Z_NOTE", 2.0)

SERVICES = env("TERRARIUM_SERVICES",
               "nodered,influxdb,grafana-server,meross-daemon,conditions-server,"
               "arduino-watchdog").split(",")


@dataclass
class Metric:
    key: str
    meas: str
    label: str
    unit: str
    digits: int
    agg: str = "mean"        # "mean" or "count" (events per window)
    min_delta: float = 0.0   # smallest change worth calling unusual
    z_floor: float = 0.1     # floor on the spread so a flat week isn't hypersensitive
    hour_floor: float = 0.0  # same floor for single hours (noisier); 0 = 3 x z_floor
    scale: float = 1.0       # e.g. 0/1 status → % of time


METRICS = [
    # Floors calibrated on about 40 days of 2026 data (analysis/timeseries): with the
    # first guesses (0.3 °C / 2 %) a normal day was flagged about 1 time in 5
    # and 13-19 % of single hours were. These values flag about 1 day in 14
    # and 1-2 % of hours.
    Metric("temp",    "local_temperature", "Temperature",  "°C",  1, min_delta=1.0, z_floor=0.7, hour_floor=1.2),
    Metric("humi",    "local_humidity",    "Humidity",     "%",   0, min_delta=4.0, z_floor=3.0, hour_floor=5.0),
    Metric("vpd",     "vpd",               "VPD",          "kPa", 2, min_delta=0.08, z_floor=0.04),
    Metric("room_t",  "room_temperature",  "Room temp",    "°C",  1, min_delta=1.0, z_floor=0.5),
    Metric("room_h",  "room_humidity",     "Room humidity","%",   0, min_delta=5.0, z_floor=3.0),
    Metric("freezer", "freezer_status",    "Freezer duty", "%",   0, min_delta=8.0, z_floor=6.0, scale=100.0),
    Metric("power",   "power_consumption", "Power",        "W",   0, min_delta=10.0, z_floor=5.0),
    Metric("mist",    "mist_event",        "Mist events",  "",    0, agg="count", min_delta=3.0, z_floor=1.5),
]
MBY = {m.key: m for m in METRICS}


# ── Small stats helpers ─────────────────────────────────────────────────

def median(xs):
    xs = sorted(x for x in xs if x is not None)
    n = len(xs)
    if n == 0:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def robust_z(x, ref, floor):
    ref = [r for r in ref if r is not None]
    if x is None or len(ref) < 3:
        return None
    m = median(ref)
    spread = 1.4826 * median([abs(r - m) for r in ref])
    return (x - m) / max(spread, floor)


def linfit(points):
    """Least squares slope/intercept for [(x, y)]."""
    n = len(points)
    if n < 2:
        return None, None
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    sxx = sum((p[0] - mx) ** 2 for p in points)
    if sxx == 0:
        return None, None
    slope = sum((p[0] - mx) * (p[1] - my) for p in points) / sxx
    return slope, my - slope * mx


SPARK = "▁▂▃▄▅▆▇█"


def sparkline(values):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    out = []
    for v in values:
        if v is None:
            out.append(" ")
        elif hi == lo:
            out.append(SPARK[3])
        else:
            out.append(SPARK[int((v - lo) / (hi - lo) * (len(SPARK) - 1) + 0.5)])
    return "".join(out)


def fmt(v, digits=1, unit=""):
    if v is None:
        return "n/a"
    s = f"{v:.{digits}f}"
    if unit:
        s += (" " if unit not in ("%", "°C") else "") + unit
    return s


def fmt_delta(v, digits=1, unit=""):
    if v is None:
        return ""
    sign = "+" if v >= 0 else "−"
    return f"{sign}{fmt(abs(v), digits, unit)}"


def fmt_dur(seconds):
    if seconds is None:
        return "n/a"
    m = int(round(seconds / 60))
    if m < 60:
        return f"{m} min"
    h, m = divmod(m, 60)
    if h < 48:
        return f"{h} h {m:02d}" if m else f"{h} h"
    return f"{h / 24:.1f} d"


def local(ts):
    return datetime.fromtimestamp(ts, TZ)


def hhmm(ts):
    return local(ts).strftime("%H:%M")


# ── Data access ─────────────────────────────────────────────────────────

class Influx:
    def __init__(self, url=INFLUX_URL, db=INFLUX_DB):
        self.url, self.db = url, db
        self.errors = []

    def series(self, q):
        """Run a query; return {measurement: [row, ...]} with epoch-second times."""
        url = (f"{self.url}/query?db={self.db}&epoch=s&q="
               f"{urllib.parse.quote(q)}")
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.load(r)
        except Exception as e:
            self.errors.append(f"{e} :: {q[:80]}")
            return {}
        out = {}
        for res in data.get("results", []):
            if "error" in res:
                self.errors.append(f"{res['error']} :: {q[:80]}")
            for s in res.get("series", []) or []:
                out[s["name"]] = [list(v) for v in s["values"]]
        return out

    def hourly(self, meas, hours, agg):
        if agg == "count":
            q = (f"SELECT count(value) FROM {meas} WHERE time > now() - {hours}h "
                 f"GROUP BY time(1h) fill(0)")
        else:
            q = (f"SELECT mean(value), min(value), max(value), count(value) FROM {meas} "
                 f"WHERE time > now() - {hours}h GROUP BY time(1h) fill(none)")
        return self.series(q).get(meas, [])

    def last_values(self, measurements, window="15m"):
        q = f"SELECT last(value) FROM {', '.join(measurements)} WHERE time > now() - {window}"
        return {k: (v[0][1], v[0][0]) for k, v in self.series(q).items() if v}

    def minute_state(self, meas, hours):
        q = (f"SELECT last(value) FROM {meas} WHERE time > now() - {hours}h "
             f"GROUP BY time(1m) fill(previous)")
        return self.series(q).get(meas, [])

    def pair_5m(self, a, b, hours):
        q = (f"SELECT mean(value) FROM {a}, {b} WHERE time > now() - {hours}h "
             f"GROUP BY time(5m) fill(none)")
        s = self.series(q)
        return s.get(a, []), s.get(b, [])


def in_window(ts, now, hours, offset_days=0, bucket=3600):
    """True if a bucket starting at ts has its midpoint inside the window."""
    end = now - offset_days * 86400
    mid = ts + bucket / 2
    return end - hours * 3600 <= mid < end


# ── Analyses ────────────────────────────────────────────────────────────

@dataclass
class Finding:
    level: str      # "red" | "yellow" | "info"
    key: str        # stable id, used to diff against the previous report
    title: str      # short; used in the subject line
    detail: str = ""


@dataclass
class Report:
    generated: float
    hours: int
    status: str = "green"
    headline: str = ""
    summary: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    freezer: dict = field(default_factory=dict)
    bands: dict = field(default_factory=dict)
    water: dict = field(default_factory=dict)
    episodes: list = field(default_factory=list)
    data: dict = field(default_factory=dict)
    system: dict = field(default_factory=dict)
    changes: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)


def analyse_metric(ix, m, now, hours, now_value):
    total_h = hours + 24 * BASELINE_DAYS + 1
    rows = ix.hourly(m.meas, total_h, m.agg)

    def agg_for(offset):
        sel = [r for r in rows if in_window(r[0], now, hours, offset)]
        if not sel:
            return None, sel
        if m.agg == "count":
            if offset and sum(1 for _ in sel) < hours * 0.5:
                return None, sel
            return float(sum(r[1] or 0 for r in sel)), sel
        if offset and len(sel) < hours * 0.5:
            return None, sel  # too little data that day to compare
        n = sum(r[4] or 0 for r in sel)
        if n == 0:
            return None, sel
        return sum((r[1] or 0) * (r[4] or 0) for r in sel) / n * m.scale, sel

    value, cur = agg_for(0)
    base = [agg_for(k)[0] for k in range(1, BASELINE_DAYS + 1)]
    expected = median(base)
    z = robust_z(value, base, m.z_floor)
    delta = (value - expected) if (value is not None and expected is not None) else None

    out = {
        "label": m.label, "unit": m.unit, "digits": m.digits,
        "value": value, "expected": expected, "delta": delta, "z": z,
        "baseline_n": sum(1 for b in base if b is not None),
        "daily": list(reversed(base)) + [value],   # oldest → today
        "now": now_value * m.scale if now_value is not None else None,
    }

    if m.agg == "count":
        out["hourly"] = [r[1] for r in sorted(cur)]
        return out

    # Window range with the hour it happened
    mins = [(r[2], r[0]) for r in cur if r[2] is not None]
    maxs = [(r[3], r[0]) for r in cur if r[3] is not None]
    if mins:
        lo = min(mins)
        out["min"], out["min_at"] = lo[0] * m.scale, lo[1]
    if maxs:
        hi = max(maxs)
        out["max"], out["max_at"] = hi[0] * m.scale, hi[1]
    out["hourly"] = [r[1] * m.scale if r[1] is not None else None for r in sorted(cur)]

    # Hour-by-hour: which hours were off compared with the same hour on prior days
    by_ts = {r[0]: r for r in rows}
    odd = []
    for r in cur:
        ref = []
        for k in range(1, BASELINE_DAYS + 1):
            b = by_ts.get(r[0] - k * 86400)
            if b and b[1] is not None:
                ref.append(b[1] * m.scale)
        if r[1] is None:
            continue
        v = r[1] * m.scale
        hz = robust_z(v, ref, m.hour_floor or 3 * m.z_floor)
        if hz is not None and abs(hz) >= Z_WARN and abs(v - median(ref)) >= m.min_delta:
            odd.append({"ts": r[0], "value": v, "expected": median(ref), "z": hz})
    out["odd_hours"] = odd

    # Completeness: compare sample count with what this channel normally logs
    counts = [r[4] for r in rows if r[4] and not in_window(r[0], now, hours)]
    typical = median(counts)
    got = sum(r[4] or 0 for r in cur)
    out["completeness"] = (got / (typical * hours)) if typical else None
    return out


def analyse_freezer(ix, now, hours):
    rows = ix.minute_state("freezer_status", hours + 24 * BASELINE_DAYS)

    def cycles_for(offset):
        sel = [r for r in rows if in_window(r[0], now, hours, offset, bucket=60)]
        if len(sel) < hours * 60 * 0.5:
            return None
        runs, start, prev = [], None, None
        for ts, v in sel:
            on = (v == 1)
            if on and not prev:
                start = ts
            if not on and prev and start is not None:
                runs.append(ts - start)
                start = None
            prev = on
        ongoing = (ts - start + 60) if (prev and start is not None) else None
        all_runs = runs + ([ongoing] if ongoing else [])
        return {
            "cycles": len(runs) + (1 if ongoing else 0),
            "short": sum(1 for r in runs if r < SHORT_CYCLE_MIN * 60),
            "longest": max(all_runs) if all_runs else 0,
            "median_run": median(all_runs),
            "on_now_for": ongoing,
        }

    cur = cycles_for(0) or {}
    base = [cycles_for(k) for k in range(1, BASELINE_DAYS + 1)]
    base_cycles = [b["cycles"] for b in base if b]
    cur["cycles_expected"] = median(base_cycles)
    cur["cycles_z"] = robust_z(cur.get("cycles"), base_cycles, 2.0)
    return cur


def analyse_bands(ix, now, hours):
    out = {}
    total = hours + 24 * BASELINE_DAYS
    specs = [("temp", "local_temperature", "target_temperature_computed", TEMP_BAND),
             ("humi", "local_humidity", "target_humidity_computed", HUMI_BAND)]
    gaps = []
    for key, a, b, tol in specs:
        sa, sb = ix.pair_5m(a, b, total)
        tgt = {r[0]: r[1] for r in sb}

        def band_for(offset):
            pts = [(r[1], tgt[r[0]]) for r in sa
                   if r[0] in tgt and r[1] is not None and tgt[r[0]] is not None
                   and in_window(r[0], now, hours, offset, bucket=300)]
            if len(pts) < hours * 6:   # < half the 5-min buckets
                return None
            inb = sum(1 for v, t in pts if abs(v - t) <= tol) / len(pts) * 100
            err = sum(v - t for v, t in pts) / len(pts)
            below = sum(1 for v, t in pts if v < t - tol) / len(pts) * 100
            above = sum(1 for v, t in pts if v > t + tol) / len(pts) * 100
            return {"in_band": inb, "mean_error": err, "below": below, "above": above,
                    "target": median([t for _, t in pts])}

        cur = band_for(0) or {}
        base = [band_for(k) for k in range(1, BASELINE_DAYS + 1)]
        cur["in_band_expected"] = median([x["in_band"] for x in base if x])
        cur["tolerance"] = tol
        out[key] = cur

        if key == "temp":
            # Data gaps in the main sensor channel (5-min buckets with no samples)
            have = {r[0] for r in sa if in_window(r[0], now, hours, 0, bucket=300)}
            start = int((now - hours * 3600) // 300 * 300) + 300
            run_start = None
            t = start
            while t < now - 300:
                if t not in have:
                    run_start = run_start or t
                elif run_start:
                    gaps.append({"start": run_start, "minutes": (t - run_start) / 60})
                    run_start = None
                t += 300
            if run_start:
                gaps.append({"start": run_start, "minutes": (t - run_start) / 60,
                             "ongoing": True})
    out["_gaps"] = [g for g in gaps if g["minutes"] >= 15]
    return out


def read_ledger(since):
    """terrarium-health.py appends one JSON line per 5-min cycle."""
    rows = []
    try:
        with open(LEDGER_FILE) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("ts", 0) >= since:
                    rows.append(r)
    except FileNotFoundError:
        return None
    return rows


def alert_class(msg):
    return re.sub(r"-?\d+(?:\.\d+)?", "#", msg)


def analyse_episodes(ledger, now, hours):
    """Group repeated warnings into episodes with start, end and duration."""
    if ledger is None:
        return None
    start_w = now - hours * 3600
    open_eps, done = {}, []
    last_ts = None
    for r in ledger:
        ts = r["ts"]
        seen = set()
        for level, msg in r.get("warnings", []):
            c = alert_class(msg)
            seen.add(c)
            ep = open_eps.get(c)
            if ep is None:
                open_eps[c] = {"start": ts, "end": ts, "level": level, "msg": msg, "n": 1}
            else:
                ep["end"], ep["msg"], ep["n"] = ts, msg, ep["n"] + 1
                if level == "red":
                    ep["level"] = "red"
        for c in list(open_eps):
            # Tolerate one missed cycle before closing an episode
            if c not in seen and ts - open_eps[c]["end"] > 11 * 60:
                done.append(open_eps.pop(c))
        last_ts = ts
    for c, ep in open_eps.items():
        ep["ongoing"] = last_ts is not None and ep["end"] >= last_ts - 60
        done.append(ep)
    eps = [e for e in done if e["end"] >= start_w]
    for e in eps:
        e["duration"] = e["end"] - e["start"] + 300
        e.setdefault("ongoing", False)
    eps.sort(key=lambda e: (e["level"] != "red", -e["start"]))
    return eps


def analyse_water(ledger, now):
    out = {}
    if not ledger:
        return out
    pts = [(r["ts"], r["water"]) for r in ledger
           if r.get("water") is not None and r["ts"] >= now - 3 * 86400]
    if not pts:
        return out
    out["level"], out["at"] = pts[-1][1], pts[-1][0]
    # Find the last refill (a jump up of > 5 pp) and fit only after it
    seg_start = 0
    refills = []
    for i in range(1, len(pts)):
        if pts[i][1] - pts[i - 1][1] > 5:
            seg_start = i
            refills.append(pts[i][0])
    out["last_refill"] = refills[-1] if refills else None
    seg = pts[seg_start:]
    span_h = (seg[-1][0] - seg[0][0]) / 3600 if len(seg) > 1 else 0
    out["fit_hours"] = span_h
    if len(seg) >= 12 and span_h >= 6:
        slope, icpt = linfit([((t - now) / 86400, v) for t, v in seg])
        if slope is not None:
            out["per_day"] = slope
            level_now = icpt  # fitted level at now (x = 0)
            out["level_fit"] = level_now
            if slope < -0.2:
                out["days_to_warn"] = max(0.0, (level_now - WATER_WARN) / -slope)
                out["days_to_empty"] = max(0.0, level_now / -slope)
    return out


def run_cmd(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def analyse_system(prev_snaps, now):
    out = {"services": {s: run_cmd(["systemctl", "is-active", s]) or "unknown"
                        for s in SERVICES}}
    try:
        du = shutil.disk_usage("/")
        out["disk_pct"] = du.used / du.total * 100
        out["disk_free_gb"] = du.free / 1e9
    except OSError:
        pass
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                mem[k] = int(v.split()[0])
        out["mem_avail_pct"] = mem["MemAvailable"] / mem["MemTotal"] * 100
    except (OSError, KeyError, ValueError):
        pass
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            out["cpu_temp"] = int(f.read()) / 1000
    except (OSError, ValueError):
        pass
    try:
        with open("/proc/uptime") as f:
            out["uptime_s"] = float(f.read().split()[0])
    except (OSError, ValueError):
        pass
    thr = run_cmd(["vcgencmd", "get_throttled"])
    if thr.startswith("throttled="):
        bits = int(thr.split("=")[1], 16)
        out["throttled_now"] = bool(bits & 0x5)
        out["undervoltage_since_boot"] = bool(bits & 0x10000)
        out["throttled_since_boot"] = bool(bits & 0x40000)

    # Disk growth from previous snapshots → days until DISK_WARN_PCT
    pts = [(s["generated"], s["system"].get("disk_pct")) for s in prev_snaps
           if s.get("system", {}).get("disk_pct") is not None
           and s["generated"] >= now - 14 * 86400]
    if "disk_pct" in out:
        pts.append((now, out["disk_pct"]))
    if len(pts) >= 4 and pts[-1][0] - pts[0][0] > 3 * 86400:
        slope, _ = linfit([((t - now) / 86400, v) for t, v in pts])
        if slope:
            out["disk_pct_per_day"] = slope
            if slope > 0.01 and out.get("disk_pct", 100) < DISK_WARN_PCT:
                out["days_to_disk_warn"] = (DISK_WARN_PCT - out["disk_pct"]) / slope
    return out


# ── Snapshots ───────────────────────────────────────────────────────────

def load_snapshots(now, days=14):
    snaps = []
    for p in sorted(glob.glob(os.path.join(SNAP_DIR, "report-*.json"))):
        try:
            with open(p) as f:
                s = json.load(f)
            if s.get("generated", 0) >= now - days * 86400:
                snaps.append(s)
        except (OSError, ValueError):
            continue
    return snaps


def save_snapshot(rep):
    os.makedirs(SNAP_DIR, exist_ok=True)
    name = local(rep.generated).strftime("report-%Y%m%d-%H%M.json")
    with open(os.path.join(SNAP_DIR, name), "w") as f:
        json.dump(asdict(rep), f, indent=1, default=str)
    cutoff = time.time() - SNAP_KEEP_DAYS * 86400
    for p in glob.glob(os.path.join(SNAP_DIR, "report-*.json")):
        try:
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
        except OSError:
            pass


# ── Findings & narrative ────────────────────────────────────────────────

def build_findings(rep):
    F = rep.findings
    m = rep.metrics
    add = lambda *a: F.append(Finding(*a))

    # Climate extremes
    t = m.get("temp", {})
    if t.get("max") is not None and t["max"] >= TEMP_HIGH:
        add("yellow", "temp_high", f"Peaked at {t['max']:.1f} °C",
            f"Temperature reached {t['max']:.1f} °C around {hhmm(t['max_at'])} "
            f"(limit {TEMP_HIGH:.1f} °C).")
    if t.get("min") is not None and t["min"] <= TEMP_LOW:
        add("yellow", "temp_low", f"Dropped to {t['min']:.1f} °C",
            f"Temperature fell to {t['min']:.1f} °C around {hhmm(t['min_at'])}.")
    h = m.get("humi", {})
    if h.get("min") is not None and h["min"] < HUMI_LOW:
        add("yellow", "humi_low", f"Humidity down to {h['min']:.0f} %",
            f"Humidity fell to {h['min']:.0f} % around {hhmm(h['min_at'])} "
            f"(limit {HUMI_LOW:.0f} %).")

    # Anything unusual versus the same hours on previous days
    for key in ("temp", "humi", "vpd", "freezer", "power", "mist", "room_t"):
        x = m.get(key)
        mt = MBY[key]
        if not x or x.get("z") is None or x.get("delta") is None:
            continue
        if abs(x["z"]) >= Z_WARN and abs(x["delta"]) >= mt.min_delta:
            word = "higher" if x["delta"] > 0 else "lower"
            level = "info" if key == "room_t" else "yellow"
            room_d = (m.get("room_t") or {}).get("delta")
            if key in ("freezer", "power") and x["delta"] > 0 and (room_d or 0) >= 0.8:
                level = "info"   # a warmer room explains it; see summary
            add(level, f"unusual_{key}",
                f"{mt.label} {word} than usual",
                f"{mt.label} {fmt(x['value'], mt.digits, mt.unit)} vs usual "
                f"{fmt(x['expected'], mt.digits, mt.unit)} for these hours "
                f"({fmt_delta(x['delta'], mt.digits, mt.unit)}).")
        odd = x.get("odd_hours") or []
        if key in ("temp", "humi") and len(odd) >= 2 and abs(x["z"] or 0) < Z_WARN:
            worst = max(odd, key=lambda o: abs(o["z"]))
            add("info", f"odd_hours_{key}",
                f"{mt.label}: {len(odd)} odd hours",
                f"{mt.label}: {len(odd)} hours out of pattern; biggest at {hhmm(worst['ts'])}: "
                f"{fmt(worst['value'], mt.digits, mt.unit)} vs usual "
                f"{fmt(worst['expected'], mt.digits, mt.unit)}.")

    # Mist: none at all when there usually are some
    mi = m.get("mist", {})
    if mi.get("value") == 0 and (mi.get("expected") or 0) >= 3:
        add("red", "mist_none", "No mist events",
            f"No mist events in {rep.hours} h; usually {mi['expected']:.0f}. "
            "Check pump, plug and Node-RED mist flow.")

    # Freezer behaviour
    fz = rep.freezer
    if fz.get("short", 0) >= SHORT_CYCLE_WARN:
        add("yellow", "freezer_short_cycling", f"Freezer short-cycling ({fz['short']}×)",
            f"{fz['short']} freezer runs shorter than {SHORT_CYCLE_MIN} min. "
            "Possible relay chatter or thermostat hysteresis issue.")
    if fz.get("on_now_for") and fz["on_now_for"] > 4 * 3600:
        add("yellow", "freezer_long_run", "Freezer running for hours",
            f"Freezer has been ON continuously for {fmt_dur(fz['on_now_for'])}.")

    # Target bands
    for key, label in (("temp", "Temperature"), ("humi", "Humidity")):
        b = rep.bands.get(key, {})
        if b.get("in_band") is not None and b.get("in_band_expected") is not None:
            drop = b["in_band_expected"] - b["in_band"]
            if drop >= 20:
                add("yellow", f"band_{key}", f"{label} off target more than usual",
                    f"{label} within ±{b['tolerance']:g} of target {b['in_band']:.0f} % "
                    f"of the time (usually {b['in_band_expected']:.0f} %).")

    # Water
    w = rep.water
    if w.get("level") is not None:
        if w["level"] < WATER_RED:
            add("red", "water_empty", f"Tank nearly empty ({w['level']:.0f} %)",
                "Refill now: the mister pump will run dry.")
        elif w["level"] < WATER_WARN:
            add("yellow", "water_low", f"Tank low ({w['level']:.0f} %)", "Refill soon.")
        elif w.get("days_to_warn") is not None and w["days_to_warn"] < WATER_ETA_WARN_DAYS:
            when = local(rep.generated + w["days_to_warn"] * 86400).strftime("%a %H:%M")
            add("yellow", "water_soon", f"Refill by {when}",
                f"Tank at {w['level']:.0f} %, falling {-w['per_day']:.1f} %/day; "
                f"reaches {WATER_WARN:.0f} % around {when}.")

    # Alert episodes from the 5-minute health check
    eps = rep.episodes or []
    ongoing_red = [e for e in eps if e["ongoing"] and e["level"] == "red"]
    ongoing_yel = [e for e in eps if e["ongoing"] and e["level"] != "red"]
    past_red = [e for e in eps if not e["ongoing"] and e["level"] == "red"]
    for e in ongoing_red:
        add("red", f"alert:{alert_class(e['msg'])}", e["msg"],
            f"Ongoing since {hhmm(e['start'])} ({fmt_dur(e['duration'])}).")
    for e in ongoing_yel:
        add("yellow", f"alert:{alert_class(e['msg'])}", e["msg"],
            f"Ongoing since {hhmm(e['start'])} ({fmt_dur(e['duration'])}).")
    if past_red:
        add("yellow", "past_red",
            f"Red alert at {hhmm(past_red[0]['start'])}, cleared" if len(past_red) == 1
            else f"{len(past_red)} red alerts, all cleared",
            "; ".join(f"{e['msg']} ({hhmm(e['start'])}, {fmt_dur(e['duration'])})"
                      for e in past_red[:3]))

    # Data quality
    no_data = m.get("temp", {}).get("value") is None
    if no_data:
        add("red", "influx_down", "No data from InfluxDB",
            (f"{len(rep.errors)} queries failed; first: {rep.errors[0][:120]}" if rep.errors
             else f"No temperature samples in the last {rep.hours} h."))
    for g in ([] if no_data else rep.data.get("gaps", [])):
        if g["minutes"] >= GAP_WARN_MIN:
            add("yellow", "data_gap", "Sensor data gap",
                f"No temperature data for {fmt_dur(g['minutes'] * 60)} from "
                f"{hhmm(g['start'])}{' (still missing)' if g.get('ongoing') else ''}.")
            break
    for key in ("temp", "power", "room_t"):
        c = m.get(key, {}).get("completeness")
        if c is not None and c < 0.9:
            add("yellow", f"incomplete_{key}", f"{MBY[key].label} feed incomplete",
                f"Only {c * 100:.0f} % of the usual {MBY[key].label.lower()} samples arrived.")
    nowv = rep.data.get("now_age", {})
    if not no_data and (nowv.get("room_temperature") is None
                        or nowv.get("room_temperature", 0) > 3600):
        add("yellow", "room_stale", "Room feed stale",
            "No room temperature in the last 15 min (DietPi → Influx feed).")
    if rep.errors and not no_data:
        add("yellow", "influx_errors", "InfluxDB query errors",
            f"{len(rep.errors)} queries failed; first: {rep.errors[0][:120]}")

    # System
    s = rep.system
    down = [k for k, v in s.get("services", {}).items() if v not in ("active", "unknown")]
    if down:
        add("red", "services_down", f"Service down: {', '.join(down)}",
            ", ".join(f"{k}={s['services'][k]}" for k in down))
    if s.get("disk_pct", 0) >= DISK_WARN_PCT:
        add("yellow", "disk_full", f"Disk {s['disk_pct']:.0f} % full",
            f"{s.get('disk_free_gb', 0):.1f} GB free.")
    elif s.get("days_to_disk_warn") is not None and s["days_to_disk_warn"] < 21:
        add("yellow", "disk_growth", "Disk filling up",
            f"At +{s['disk_pct_per_day']:.2f} pp/day, disk reaches {DISK_WARN_PCT:.0f} % "
            f"in ~{s['days_to_disk_warn']:.0f} days.")
    if s.get("cpu_temp", 0) >= CPU_TEMP_WARN:
        add("yellow", "cpu_hot", f"Pi CPU at {s['cpu_temp']:.0f} °C", "")
    if s.get("throttled_now") or s.get("undervoltage_since_boot"):
        add("yellow", "pi_power", "Pi under-voltage / throttling",
            "vcgencmd reports under-voltage or throttling. Check the Pi PSU.")

    order = {"red": 0, "yellow": 1, "info": 2}
    F.sort(key=lambda f: order[f.level])


def build_summary(rep):
    """Plain-language sentences: what happened and why, in order of interest."""
    S = []
    m = rep.metrics
    t, h, r, fz = m.get("temp", {}), m.get("humi", {}), m.get("room_t", {}), m.get("freezer", {})

    def vs(x, mt):
        if x.get("expected") is None or x.get("delta") is None:
            return ""
        if abs(x["delta"]) < mt.min_delta / 2:
            return " (normal for these hours)"
        return f" (usual {fmt(x['expected'], mt.digits, mt.unit)})"

    if t.get("value") is not None:
        S.append(f"Temperature averaged {fmt(t['value'], 1, '°C')}{vs(t, MBY['temp'])}, "
                 f"range {fmt(t.get('min'), 1)}–{fmt(t.get('max'), 1, '°C')}. "
                 f"Humidity {fmt(h.get('value'), 0, '%')}{vs(h, MBY['humi'])}.")
    bt, bh = rep.bands.get("temp", {}), rep.bands.get("humi", {})
    if bt.get("in_band") is not None and bh.get("in_band") is not None:
        S.append(f"On target {bt['in_band']:.0f} % of the time for temperature "
                 f"and {bh['in_band']:.0f} % for humidity"
                 + (f"; humidity was below target {bh['below']:.0f} % of the time."
                    if bh.get("below", 0) >= 10 else "."))

    if fz.get("value") is not None:
        cyc = rep.freezer.get("cycles")
        line = (f"Freezer ran {fz['value']:.0f} % of the time"
                + (f" (usual {fz['expected']:.0f} %)" if fz.get("expected") is not None else "")
                + (f" in {cyc} cycles" if cyc is not None else "") + ".")
        # Explain a busier freezer by the room, when the room explains it
        if (fz.get("delta") or 0) >= MBY["freezer"].min_delta and (r.get("delta") or 0) >= 0.8:
            line += f" Likely because the room was {r['delta']:.1f} °C warmer than usual."
        elif (fz.get("delta") or 0) >= MBY["freezer"].min_delta and (r.get("delta") is not None):
            line += " The room was not warmer, so worth a look (door seal, frost, fans)."
        S.append(line)

    p = m.get("power", {})
    if p.get("value") is not None:
        kwh = p["value"] * rep.hours / 1000
        S.append(f"Used {kwh:.2f} kWh (≈ €{kwh * KWH_PRICE:.2f})"
                 + (f", {fmt_delta(p['delta'] * rep.hours / 1000, 2)} kWh vs usual."
                    if p.get("delta") is not None else "."))

    mi = m.get("mist", {})
    if mi.get("value") is not None:
        S.append(f"{mi['value']:.0f} mist events"
                 + (f" (usual {mi['expected']:.0f})." if mi.get("expected") is not None else "."))

    w = rep.water
    if w.get("level") is not None:
        line = f"Water tank at {w['level']:.0f} %"
        if w.get("per_day") is not None and w["per_day"] < -0.2:
            line += f", using {-w['per_day']:.1f} %/day"
            if w.get("days_to_warn") is not None:
                when = local(rep.generated + w["days_to_warn"] * 86400).strftime("%a %d %b")
                line += f"; refill by {when}"
        elif w.get("per_day") is not None:
            line += ", stable"
        S.append(line + ".")

    eps = rep.episodes
    if eps is not None:
        if not eps:
            S.append("No alerts from the 5-minute health check.")
        else:
            on = sum(1 for e in eps if e["ongoing"])
            S.append(f"{len(eps)} alert episode(s) from the health check"
                     + (f", {on} still open." if on else ", all cleared."))
    rep.summary = S


def diff_previous(rep, prev):
    if not prev:
        return {}
    prev_keys = {f["key"]: f for f in prev.get("findings", []) if f["level"] != "info"}
    cur_keys = {f.key: f for f in rep.findings if f.level != "info"}
    return {
        "since": prev["generated"],
        "new": [cur_keys[k].title for k in cur_keys if k not in prev_keys],
        "cleared": [prev_keys[k]["title"] for k in prev_keys if k not in cur_keys],
        "still": [cur_keys[k].title for k in cur_keys if k in prev_keys],
    }


def make_report(ix, hours, now=None):
    now = now or time.time()
    rep = Report(generated=now, hours=hours)

    lasts = ix.last_values([m.meas for m in METRICS if m.agg != "count"]
                           + ["target_temperature_computed", "target_humidity_computed"])
    rep.data["now_age"] = {k: now - v[1] for k, v in lasts.items()}
    for m in METRICS:
        rep.metrics[m.key] = analyse_metric(ix, m, now, hours,
                                            lasts.get(m.meas, (None, 0))[0])
    rep.data["targets"] = {
        "temp": lasts.get("target_temperature_computed", (None, 0))[0],
        "humi": lasts.get("target_humidity_computed", (None, 0))[0],
    }
    rep.freezer = analyse_freezer(ix, now, hours)
    rep.bands = analyse_bands(ix, now, hours)
    rep.data["gaps"] = rep.bands.pop("_gaps", [])

    ledger = read_ledger(now - 3 * 86400)
    rep.data["ledger"] = ledger is not None
    rep.episodes = analyse_episodes(ledger, now, hours)
    rep.water = analyse_water(ledger, now)

    snaps = load_snapshots(now)
    rep.system = analyse_system(snaps, now)
    rep.errors = ix.errors

    build_findings(rep)
    build_summary(rep)
    prev = snaps[-1] if snaps else None
    rep.changes = diff_previous(rep, prev)

    levels = {f.level for f in rep.findings}
    rep.status = "red" if "red" in levels else ("yellow" if "yellow" in levels else "green")
    issues = [f for f in rep.findings if f.level in ("red", "yellow")]
    if not issues:
        bits = ["All normal"]
        if t := rep.metrics.get("temp", {}).get("now"):
            bits.append(f"{t:.1f} °C")
        if hm := rep.metrics.get("humi", {}).get("now"):
            bits.append(f"{hm:.0f} %")
        if rep.water.get("days_to_warn") is not None:
            bits.append(f"refill in {rep.water['days_to_warn']:.0f} d")
        rep.headline = " · ".join(bits)
    else:
        rep.headline = "; ".join(f.title for f in issues[:2])
        if len(issues) > 2:
            rep.headline += f" (+{len(issues) - 2} more)"
    return rep


# ── Rendering ───────────────────────────────────────────────────────────

EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴", "info": "ℹ️"}
COL = {  # text, background, border
    "green":  ("#1b5e20", "#e8f5e9", "#2e7d32"),
    "yellow": ("#7a4b00", "#fff4e0", "#e0a030"),
    "red":    ("#8e1b1b", "#fdecea", "#c62828"),
    "info":   ("#24476b", "#eaf2fb", "#5b8bc0"),
}


def subject_line(rep):
    kind = "daily report" if rep.hours >= 20 else f"{rep.hours} h report"
    return f"{EMOJI[rep.status]} Terrarium {kind} · {rep.headline}"


def metric_rows(rep):
    rows = []
    for key in ("temp", "humi", "vpd", "freezer", "power", "mist", "room_t", "room_h"):
        x = rep.metrics.get(key)
        if not x:
            continue
        mt = MBY[key]
        d = x.get("delta")
        z = x.get("z")
        flag = ""
        if z is not None and d is not None and abs(d) >= mt.min_delta:
            if abs(z) >= Z_WARN:
                flag = "yellow"
            elif abs(z) >= Z_NOTE:
                flag = "info"
        rng = ""
        if x.get("min") is not None:
            rng = f"{fmt(x['min'], mt.digits)}–{fmt(x['max'], mt.digits)}"
        rows.append({
            "label": mt.label,
            "now": fmt(x.get("now"), mt.digits, mt.unit) if mt.agg != "count" else "",
            "avg": fmt(x.get("value"), mt.digits, mt.unit),
            "usual": fmt(x.get("expected"), mt.digits, mt.unit),
            "delta": fmt_delta(d, mt.digits, mt.unit) if d is not None else "",
            "range": rng,
            "hours": sparkline(x.get("hourly") or []),
            "days": sparkline(x.get("daily") or []),
            "flag": flag,
        })
    return rows


def render_text(rep):
    L = []
    when = local(rep.generated).strftime("%a %d %b %Y %H:%M")
    L.append(f"{EMOJI[rep.status]} TERRARIUM: {rep.headline}")
    L.append(f"{when}, last {rep.hours} h, compared with the same hours on the previous "
             f"{BASELINE_DAYS} days")
    L.append("")
    issues = [f for f in rep.findings if f.level in ("red", "yellow")]
    if issues:
        L.append("NEEDS ATTENTION")
        for f in issues:
            L.append(f"  {EMOJI[f.level]} {f.title}" + (f": {f.detail}" if f.detail else ""))
        L.append("")
    ch = rep.changes
    if ch and (ch.get("new") or ch.get("cleared")):
        L.append(f"SINCE LAST REPORT ({hhmm(ch['since'])})")
        for t in ch.get("new", []):
            L.append(f"  new:     {t}")
        for t in ch.get("cleared", []):
            L.append(f"  cleared: {t}")
        L.append("")
    L.append("SUMMARY")
    for s in rep.summary:
        L.append(f"  • {s}")
    notes = [f for f in rep.findings if f.level == "info"]
    for f in notes:
        L.append(f"  ℹ {f.detail or f.title}")
    L.append("")
    L.append("NUMBERS (window avg vs usual)        hourly     8 days")
    for r in metric_rows(rep):
        mark = {"yellow": "!", "info": "~"}.get(r["flag"], " ")
        L.append(f" {mark}{r['label']:<14}{r['avg']:>9}  usual {r['usual']:>9} {r['delta']:>9}"
                 f"  {r['hours'][-24:]:<24}  {r['days']}")
    fz = rep.freezer
    if fz:
        L.append("")
        L.append(f"FREEZER  {fz.get('cycles', 'n/a')} cycles (usual {fmt(fz.get('cycles_expected'), 0)}), "
                 f"{fz.get('short', 0)} short, longest {fmt_dur(fz.get('longest'))}, "
                 f"median run {fmt_dur(fz.get('median_run'))}")
    if rep.episodes:
        L.append("")
        L.append("ALERT EPISODES")
        for e in rep.episodes:
            st = "ongoing" if e["ongoing"] else f"until {hhmm(e['end'])}"
            L.append(f"  {EMOJI[e['level']]} {hhmm(e['start'])} {st:>13}  {fmt_dur(e['duration']):>8}  {e['msg']}")
    s = rep.system
    L.append("")
    svc = s.get("services", {})
    bad = [k for k, v in svc.items() if v != "active"]
    L.append("SYSTEM   services " + ("all active" if not bad else ", ".join(f"{k}={svc[k]}" for k in bad))
             + f" · disk {fmt(s.get('disk_pct'), 0, '%')}"
             + f" · CPU {fmt(s.get('cpu_temp'), 0, '°C')}"
             + f" · up {fmt_dur(s.get('uptime_s'))}")
    if not rep.data.get("ledger"):
        L.append("  (health ledger not found: alert episodes and water trend unavailable)")
    return "\n".join(L)


def render_html(rep):
    e = html.escape
    tc, bg, bd = COL[rep.status]
    when = local(rep.generated).strftime("%a %d %b %Y, %H:%M")
    font = "-apple-system,Segoe UI,Helvetica,Arial,sans-serif"
    mono = "SFMono-Regular,Menlo,Consolas,monospace"
    P = []
    P.append(f'<div style="font-family:{font};color:#1f2328;max-width:680px;margin:0 auto;'
             f'line-height:1.45;font-size:14px">')
    # Banner
    P.append(f'<div style="background:{bg};border-left:6px solid {bd};padding:14px 16px;'
             f'border-radius:6px;margin-bottom:14px">'
             f'<div style="font-size:12px;color:#57606a;text-transform:uppercase;letter-spacing:.04em">'
             f'Terrarium · {"daily report" if rep.hours >= 20 else f"last {rep.hours} h"} · {e(when)}</div>'
             f'<div style="font-size:19px;font-weight:600;color:{tc};margin-top:4px">'
             f'{EMOJI[rep.status]} {e(rep.headline)}</div></div>')

    # Needs attention
    issues = [f for f in rep.findings if f.level in ("red", "yellow")]
    if issues:
        P.append('<h3 style="margin:16px 0 6px;font-size:15px">Needs attention</h3>')
        for f in issues:
            c = COL[f.level]
            P.append(f'<div style="background:{c[1]};border-left:4px solid {c[2]};padding:8px 12px;'
                     f'margin:6px 0;border-radius:4px"><b style="color:{c[0]}">{EMOJI[f.level]} '
                     f'{e(f.title)}</b>' + (f'<br><span style="color:#424a53">{e(f.detail)}</span>'
                                            if f.detail else "") + '</div>')

    ch = rep.changes
    if ch and (ch.get("new") or ch.get("cleared")):
        items = ([f'<span style="color:#8e1b1b">new</span> {e(t)}' for t in ch["new"]]
                 + [f'<span style="color:#1b5e20">cleared</span> {e(t)}' for t in ch["cleared"]])
        P.append(f'<div style="font-size:13px;color:#57606a;margin:10px 0">Since last report '
                 f'({e(hhmm(ch["since"]))}): ' + " · ".join(items) + '</div>')

    # Summary
    P.append('<h3 style="margin:16px 0 6px;font-size:15px">Summary</h3><ul style="margin:0;padding-left:20px">')
    for s in rep.summary:
        P.append(f'<li style="margin:3px 0">{e(s)}</li>')
    for f in rep.findings:
        if f.level == "info":
            P.append(f'<li style="margin:3px 0;color:#24476b">{e(f.detail or f.title)}</li>')
    P.append('</ul>')

    # Numbers table
    th = 'style="text-align:left;padding:6px 8px;border-bottom:2px solid #d0d7de;font-size:12px;color:#57606a;font-weight:600"'
    thr = th.replace("text-align:left", "text-align:right")
    td = 'style="padding:6px 8px;border-bottom:1px solid #eaeef2;vertical-align:middle"'
    tdr = td.replace("padding", "text-align:right;padding")
    tds = (f'style="padding:6px 8px;border-bottom:1px solid #eaeef2;font-family:{mono};'
           f'color:#5b8bc0;letter-spacing:-1px;white-space:nowrap"')
    P.append(f'<h3 style="margin:18px 0 6px;font-size:15px">Numbers</h3>'
             f'<div style="font-size:12px;color:#57606a;margin-bottom:4px">Average over the last '
             f'{rep.hours} h vs the median of the same hours on the previous {BASELINE_DAYS} days. '
             f'Sparklines: hour by hour, then one value per day for 8 days.</div>'
             f'<table style="border-collapse:collapse;width:100%;font-size:13px">'
             f'<tr><th {th}></th><th {thr}>Avg</th><th {thr}>Usual</th><th {thr}>Δ</th></tr>')
    top = td.replace("border-bottom:1px solid #eaeef2;", "padding-bottom:0;")
    topr = tdr.replace("border-bottom:1px solid #eaeef2;", "padding-bottom:0;")
    for r in metric_rows(rep):
        hl = f'background:{COL[r["flag"]][1]};' if r["flag"] else ""
        sub = []
        if r["now"]:
            sub.append(f"now {e(r['now'])}")
        if r["range"]:
            sub.append(f"range {e(r['range'])}")
        spark = (f'<span style="font-family:{mono};color:#5b8bc0;letter-spacing:-1px;'
                 f'white-space:nowrap">{e(r["hours"][-24:])}</span>'
                 f'&nbsp;&nbsp;<span style="font-family:{mono};color:#8c959f;letter-spacing:-1px;'
                 f'white-space:nowrap">{e(r["days"])}</span>')
        P.append(f'<tr style="{hl}"><td {top}><b>{e(r["label"])}</b></td>'
                 f'<td {topr}><b>{e(r["avg"])}</b></td>'
                 f'<td {topr}><span style="color:#57606a">{e(r["usual"])}</span></td>'
                 f'<td {topr}>{e(r["delta"])}</td></tr>'
                 f'<tr style="{hl}"><td colspan="4" style="padding:0 8px 6px;border-bottom:1px solid #eaeef2;'
                 f'font-size:12px;color:#57606a">{" · ".join(sub)}'
                 f'{"<br>" if sub else ""}{spark}</td></tr>')
    P.append('</table>')

    # Equipment + control quality
    fz, bt, bh = rep.freezer, rep.bands.get("temp", {}), rep.bands.get("humi", {})
    kv = []
    if fz:
        kv.append(("Freezer cycles", f"{fz.get('cycles', 'n/a')} (usual {fmt(fz.get('cycles_expected'), 0)}), "
                   f"{fz.get('short', 0)} under {SHORT_CYCLE_MIN} min, longest {fmt_dur(fz.get('longest'))}"
                   + (f", ON now for {fmt_dur(fz['on_now_for'])}" if fz.get("on_now_for") else "")))
    if bt.get("in_band") is not None:
        kv.append(("Temp on target", f"{bt['in_band']:.0f} % within ±{bt['tolerance']:g} °C "
                   f"(usual {fmt(bt.get('in_band_expected'), 0, '%')}), mean error {fmt_delta(bt['mean_error'], 2, '°C')}"))
    if bh.get("in_band") is not None:
        kv.append(("Humidity on target", f"{bh['in_band']:.0f} % within ±{bh['tolerance']:g} pp "
                   f"(usual {fmt(bh.get('in_band_expected'), 0, '%')}), below {bh['below']:.0f} %, above {bh['above']:.0f} %"))
    w = rep.water
    if w.get("level") is not None:
        txt = f"{w['level']:.0f} %"
        if w.get("per_day") is not None:
            txt += f", {fmt_delta(w['per_day'], 1)} %/day"
        if w.get("days_to_warn") is not None:
            txt += (f", reaches {WATER_WARN:.0f} % "
                    f"{local(rep.generated + w['days_to_warn'] * 86400).strftime('%a %d %b %H:%M')}")
        if w.get("last_refill"):
            txt += f" · last refill {local(w['last_refill']).strftime('%a %H:%M')}"
        kv.append(("Water tank", txt))
    if kv:
        P.append('<h3 style="margin:18px 0 6px;font-size:15px">Equipment & control</h3>'
                 '<table style="border-collapse:collapse;width:100%;font-size:13px">')
        for k, v in kv:
            P.append(f'<tr><td {td} width="32%"><b>{e(k)}</b></td><td {td}>{e(v)}</td></tr>')
        P.append('</table>')

    # Alert episodes
    if rep.episodes:
        P.append('<h3 style="margin:18px 0 6px;font-size:15px">Alert episodes</h3>'
                 '<table style="border-collapse:collapse;width:100%;font-size:13px">'
                 f'<tr><th {th}></th><th {th}>From</th><th {th}>Until</th><th {th}>Length</th><th {th}>Alert</th></tr>')
        for ep in rep.episodes:
            until = "<b>ongoing</b>" if ep["ongoing"] else e(hhmm(ep["end"]))
            P.append(f'<tr><td {td}>{EMOJI[ep["level"]]}</td><td {td}>{e(local(ep["start"]).strftime("%a %H:%M"))}</td>'
                     f'<td {td}>{until}</td><td {td}>{e(fmt_dur(ep["duration"]))}</td><td {td}>{e(ep["msg"])}</td></tr>')
        P.append('</table>')

    # System
    s = rep.system
    svc = s.get("services", {})
    svc_html = " ".join(
        f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:1px 7px;border-radius:10px;font-size:12px;'
        f'background:{COL["green" if v == "active" else ("info" if v == "unknown" else "red")][1]}">'
        f'{e(k)}</span>' for k, v in svc.items())
    sysline = (f"disk {fmt(s.get('disk_pct'), 0, '%')}"
               + (f" ({fmt_delta(s['disk_pct_per_day'], 2)} pp/day)" if s.get("disk_pct_per_day") is not None else "")
               + f" · RAM free {fmt(s.get('mem_avail_pct'), 0, '%')}"
               + f" · CPU {fmt(s.get('cpu_temp'), 0, '°C')}"
               + f" · up {fmt_dur(s.get('uptime_s'))}")
    gaps = rep.data.get("gaps", [])
    gap_txt = ("no gaps" if not gaps else
               f"{len(gaps)} gap(s), longest {fmt_dur(max(g['minutes'] for g in gaps) * 60)}")
    comp = rep.metrics.get("temp", {}).get("completeness")
    P.append('<h3 style="margin:18px 0 6px;font-size:15px">System & data</h3>'
             f'<div style="font-size:13px">{svc_html}</div>'
             f'<div style="font-size:13px;color:#424a53;margin-top:4px">{e(sysline)}</div>'
             f'<div style="font-size:13px;color:#424a53">Sensor data: '
             f'{e(fmt(comp * 100 if comp is not None else None, 0, "%"))} complete, {e(gap_txt)}</div>')
    if not rep.data.get("ledger"):
        P.append('<div style="font-size:12px;color:#7a4b00;margin-top:4px">Health ledger not found, '
                 'so alert episodes and the water trend are missing. Deploy the updated terrarium-health.py.</div>')

    P.append(f'<div style="font-size:11px;color:#8c959f;margin-top:20px;border-top:1px solid #eaeef2;padding-top:8px">'
             f'terrarium-report.py · "Usual" = median of the same {rep.hours} h window on each of the previous '
             f'{BASELINE_DAYS} days; flagged when the robust z-score is ≥ {Z_WARN:g} and the change is large '
             f'enough to matter. Tune thresholds in /etc/terrarium/secrets.env.</div></div>')
    return "<html><body style=\"margin:0;padding:12px;background:#ffffff\">" + "".join(P) + "</body></html>"


def to_json(rep):
    return json.dumps(asdict(rep), indent=1, default=str)


# ── Email ───────────────────────────────────────────────────────────────

def send_email(rep):
    addr = os.environ.get("TERRARIUM_GMAIL_ADDRESS")
    pw = os.environ.get("TERRARIUM_GMAIL_APP_PASS")
    to = os.environ.get("TERRARIUM_REPORT_TO") or os.environ.get("TERRARIUM_GMAIL_TO")
    if not (addr and pw and to):
        print("email not configured: set TERRARIUM_GMAIL_ADDRESS, TERRARIUM_GMAIL_APP_PASS "
              "and TERRARIUM_GMAIL_TO in /etc/terrarium/secrets.env", file=sys.stderr)
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject_line(rep)
    msg["From"] = addr
    msg["To"] = to
    msg.attach(MIMEText(render_text(rep), "plain", "utf-8"))
    msg.attach(MIMEText(render_html(rep), "html", "utf-8"))
    for attempt in range(3):
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
                s.starttls()
                s.login(addr, pw)
                s.send_message(msg, to_addrs=[a.strip() for a in to.split(",")])
            return True
        except Exception as ex:
            print(f"send failed (attempt {attempt + 1}): {ex}", file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--hours", type=int, default=24, help="report window (default 24)")
    ap.add_argument("--format", choices=["text", "html", "json"], default="text")
    ap.add_argument("--email", action="store_true", help="send by email and save a snapshot")
    ap.add_argument("--quiet-if-green", action="store_true",
                    help="with --email: skip sending when all green and nothing changed")
    ap.add_argument("--no-save", action="store_true", help="don't write a snapshot")
    args = ap.parse_args()

    rep = make_report(Influx(), args.hours)

    if args.email:
        changed = bool(rep.changes.get("new") or rep.changes.get("cleared"))
        if args.quiet_if_green and rep.status == "green" and not changed:
            print(f"quiet: {subject_line(rep)}")
            ok = True
        else:
            ok = send_email(rep)
            print(("sent: " if ok else "FAILED: ") + subject_line(rep))
        if not args.no_save:
            save_snapshot(rep)
        sys.exit(0 if ok else 1)

    out = {"text": render_text, "html": render_html, "json": to_json}[args.format](rep)
    print(out)


if __name__ == "__main__":
    main()
