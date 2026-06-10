#!/usr/bin/env python3
"""Generate publication figures for the HardwareX manuscript from InfluxDB.

Produces, into ../paper/figures/:
  fig1_environmental_24h.png   representative 24 h cabinet cycle (T/RH/VPD vs targets + room)
  fig2_environmental_7d.png    representative 7 d cycle (stochastic weather-driven setpoints)
  fig3_power_profile.png       hour-of-day power profile + distribution (Meross window)
  fig4_pid_response.png        a representative day of humidity tracking + PID fan response
  fig5_safety_chain_timeline.png  11-layer safety chain by deployment date

InfluxDB only (no extra services). Re-run any time; windows for fig1/2/4 are
the most recent clean span, fig3 is pinned to the 80.3-day Meross window so it
matches HardwareX Section 7.7. Captions in the manuscript state the window.

Usage:  python3 publication_figures.py
"""
import json
import os
import datetime as dt
import urllib.parse
import urllib.request

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

INFLUX = "http://localhost:8086/query"
DB = "highland"
ADB = "highland_archive"
OUT = os.path.join(os.path.dirname(__file__), "..", "paper", "figures")
os.makedirs(OUT, exist_ok=True)

# Site palette (kept consistent with the live dashboards)
C_CAB = "#b06dd1"   # cabinet / primary accent
C_TGT = "#e0a030"   # target (amber)
C_ROOM = "#4c9a5a"  # room (green)
C_VPD = "#3b7dd8"   # vpd (blue)
C_FAN = "#888888"

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "figure.dpi": 160,
    "savefig.dpi": 200,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def q(database, query):
    """Run an InfluxQL query (POST) and return the first series rows or []."""
    data = urllib.parse.urlencode({"db": database, "q": query}).encode()
    req = urllib.request.Request(INFLUX, data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.load(r)
    res = j["results"][0]
    if "series" not in res:
        return [], []
    s = res["series"][0]
    return s["columns"], s["values"]


def series(database, meas, start, end, every, agg="mean", field="value"):
    """Return (times[], values[]) for a measurement, regularly grouped."""
    query = (
        f'SELECT {agg}("{field}") FROM "{meas}" '
        f"WHERE time >= '{start}' AND time <= '{end}' "
        f"GROUP BY time({every}) fill(none)"
    )
    cols, rows = q(database, query)
    ts, vs = [], []
    for t, v in rows:
        if v is None:
            continue
        ts.append(dt.datetime.fromisoformat(t.replace("Z", "+00:00")))
        vs.append(float(v))
    return np.array(ts), np.array(vs)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def shade_photoperiod(ax, times, light_t, light_v):
    """Light grey shading where the lights are ON."""
    if len(light_t) == 0:
        return
    on = light_v > 0.5
    for i in range(1, len(light_t)):
        if on[i]:
            ax.axvspan(light_t[i - 1], light_t[i], color="#f2c94c", alpha=0.07, lw=0)


# ---------------------------------------------------------------------------
def fig_environmental(window_hours, every, fname, title):
    end = now_utc()
    start = end - dt.timedelta(hours=window_hours)
    s, e = iso(start), iso(end)
    # Main DB only: 365-day retention covers every window used here, and the
    # highland_archive 1h continuous queries are not reliably populated.
    db = DB

    ct, cv = series(db, "local_temperature", s, e, every)
    tt, tv = series(db, "target_temperature_computed", s, e, every)
    rt, rv = series(db, "room_temperature", s, e, every)
    ch, cvh = series(db, "local_humidity", s, e, every)
    th, tvh = series(db, "target_humidity_computed", s, e, every)
    rh, rvh = series(db, "room_humidity", s, e, every)
    vt, vv = series(db, "vpd", s, e, every)
    lt, lv = series(db, "light_status", s, e, every)

    fig, ax = plt.subplots(3, 1, figsize=(7.0, 6.4), sharex=True)

    shade_photoperiod(ax[0], lt, lt, lv)
    ax[0].plot(ct, cv, color=C_CAB, lw=1.4, label="Cabinet")
    ax[0].plot(tt, tv, color=C_TGT, lw=1.2, ls="--", label="Target")
    ax[0].plot(rt, rv, color=C_ROOM, lw=1.0, alpha=0.8, label="Room")
    ax[0].set_ylabel("Temperature (°C)")
    ax[0].legend(loc="upper right", ncol=3, fontsize=7, framealpha=0.85)
    ax[0].set_title(title)

    shade_photoperiod(ax[1], lt, lt, lv)
    ax[1].plot(ch, cvh, color=C_CAB, lw=1.4, label="Cabinet")
    ax[1].plot(th, tvh, color=C_TGT, lw=1.2, ls="--", label="Target")
    ax[1].plot(rh, rvh, color=C_ROOM, lw=1.0, alpha=0.8, label="Room")
    ax[1].set_ylabel("Relative humidity (%)")
    ax[1].legend(loc="lower right", ncol=3, fontsize=7, framealpha=0.85)

    shade_photoperiod(ax[2], lt, lt, lv)
    ax[2].plot(vt, vv, color=C_VPD, lw=1.4)
    ax[2].set_ylabel("VPD (kPa)")
    ax[2].set_xlabel("Time (UTC)")

    if window_hours <= 48:
        ax[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax[2].xaxis.set_major_locator(mdates.HourLocator(interval=3))
    else:
        ax[2].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        ax[2].xaxis.set_major_locator(mdates.DayLocator())
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.tight_layout()
    p = os.path.join(OUT, fname)
    fig.savefig(p)
    plt.close(fig)
    print("wrote", p, f"({len(cv)} cabinet-T pts)")


# ---------------------------------------------------------------------------
def fig_power():
    """Hour-of-day profile + ECDF over the pinned Meross window."""
    s = "2026-02-18T22:12:44Z"
    e = "2026-05-10T06:26:07Z"
    # hour-of-day stats from the main DB (365-day retention covers this window;
    # the highland_archive rollups only start 2026-05-19).
    cols, rows = q(
        DB,
        f'SELECT mean("value") FROM "power_consumption" '
        f"WHERE time >= '{s}' AND time <= '{e}' GROUP BY time(1h) fill(none)",
    )
    by_hour = {h: [] for h in range(24)}
    allv = []
    for t, v in rows:
        if v is None:
            continue
        hh = dt.datetime.fromisoformat(t.replace("Z", "+00:00")).hour
        by_hour[hh].append(float(v))
        allv.append(float(v))
    hours = list(range(24))
    med = [np.median(by_hour[h]) if by_hour[h] else np.nan for h in hours]
    q25 = [np.percentile(by_hour[h], 25) if by_hour[h] else np.nan for h in hours]
    q75 = [np.percentile(by_hour[h], 75) if by_hour[h] else np.nan for h in hours]
    allv = np.array(allv)

    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.2))
    ax[0].fill_between(hours, q25, q75, color=C_CAB, alpha=0.25, label="IQR")
    ax[0].plot(hours, med, color=C_CAB, lw=1.6, label="Median")
    ax[0].set_xlabel("Hour of day (UTC)")
    ax[0].set_ylabel("Power (W)")
    ax[0].set_title("Hour-of-day power profile")
    ax[0].set_xticks(range(0, 24, 4))
    ax[0].legend(fontsize=7)

    xs = np.sort(allv)
    ys = np.arange(1, len(xs) + 1) / len(xs)
    ax[1].plot(xs, ys, color=C_VPD, lw=1.6)
    for pct, lab in [(50, "median"), (95, "p95")]:
        val = np.percentile(allv, pct)
        ax[1].axvline(val, color="#aaaaaa", ls=":", lw=1)
        ax[1].text(val, 0.04, f" {lab}\n {val:.0f} W", fontsize=6.5, rotation=0)
    ax[1].set_xlabel("Power (W)")
    ax[1].set_ylabel("Cumulative fraction")
    ax[1].set_title("Power distribution (hourly means)")
    fig.tight_layout()
    p = os.path.join(OUT, "fig3_power_profile.png")
    fig.savefig(p)
    plt.close(fig)
    print("wrote", p, f"(n={len(allv)} hourly means)")


# ---------------------------------------------------------------------------
def fig_pid():
    """Representative 24 h: humidity tracking + PID fan response + control mode."""
    end = now_utc()
    start = end - dt.timedelta(hours=24)
    s, e = iso(start), iso(end)
    ch, cvh = series(DB, "local_humidity", s, e, "5m")
    th, tvh = series(DB, "target_humidity_computed", s, e, "5m")
    ft, fv = series(DB, "fan_speed", s, e, "5m")
    mt, mv = series(DB, "pid_control_mode", s, e, "5m", agg="max")

    fig, ax1 = plt.subplots(figsize=(7.0, 3.6))
    ax1.plot(ch, cvh, color=C_CAB, lw=1.5, label="Cabinet RH")
    ax1.plot(th, tvh, color=C_TGT, lw=1.2, ls="--", label="Target RH")
    ax1.set_ylabel("Relative humidity (%)")
    ax1.set_xlabel("Time (UTC)")

    ax2 = ax1.twinx()
    ax2.plot(ft, fv, color=C_FAN, lw=1.0, alpha=0.8, label="Fan PWM")
    ax2.set_ylabel("Fan PWM (0–255)")
    ax2.set_ylim(0, 260)
    ax2.spines["right"].set_visible(True)

    # shade temperature-PID intervals
    if len(mt):
        tpid = mv > 0.5
        for i in range(1, len(mt)):
            if tpid[i]:
                ax1.axvspan(mt[i - 1], mt[i], color="#d8704c", alpha=0.10, lw=0)

    l1, lab1 = ax1.get_legend_handles_labels()
    l2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lab1 + lab2, loc="upper right", fontsize=7, framealpha=0.85)
    ax1.set_title("PID humidity tracking and fan response (representative 24 h)")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    fig.tight_layout()
    p = os.path.join(OUT, "fig4_pid_response.png")
    fig.savefig(p)
    plt.close(fig)
    print("wrote", p, f"({len(cvh)} RH pts)")


# ---------------------------------------------------------------------------
def fig_safety_chain():
    """Timeline of the 11 safety layers by deployment date (from the YAML)."""
    yaml_path = os.path.join(
        os.path.dirname(__file__), "..", "paper", "safety_chain_deployment_dates.yaml"
    )
    layers = []
    cur = {}
    try:
        with open(yaml_path) as fh:
            for line in fh:
                t = line.rstrip("\n")
                st = t.strip()
                if st.startswith("- id:"):
                    if cur.get("label") and cur.get("deployed"):
                        layers.append(cur)
                    cur = {"id": st.split("id:", 1)[1].strip().strip('"')}
                elif st.startswith("label:"):
                    cur["label"] = st.split("label:", 1)[1].strip().strip('"')
                elif st.startswith("deployed:"):
                    cur["deployed"] = st.split("deployed:", 1)[1].strip().strip('"')
                elif st.startswith("status:"):
                    cur["status"] = st.split("status:", 1)[1].strip().strip('"')
            if cur.get("label") and cur.get("deployed"):
                layers.append(cur)
    except FileNotFoundError:
        print("safety-chain YAML not found; skipping fig5")
        return

    parsed = []
    for L in layers:
        try:
            d = dt.datetime.strptime(L["deployed"][:10], "%Y-%m-%d")
        except (ValueError, KeyError):
            continue
        parsed.append((d, L.get("label", L.get("id", "?")), L.get("status", "active")))
    if not parsed:
        print("no datable safety layers; skipping fig5")
        return
    parsed.sort()

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    for i, (d, label, status) in enumerate(parsed):
        col = C_CAB if "deprecated" not in status else "#bbbbbb"
        ax.plot([d], [i], "o", color=col, ms=7)
        ax.text(d, i + 0.18, f"  {label}", fontsize=7, va="bottom")
        ax.hlines(i, parsed[0][0], d, color="#dddddd", lw=0.8, zorder=0)
    ax.set_yticks(range(len(parsed)))
    ax.set_yticklabels([f"L{i+1}" for i in range(len(parsed))], fontsize=7)
    ax.set_xlabel("Deployment date")
    ax.set_title("Safety-chain evolution — 11 layers by deployment date")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.margins(x=0.02, y=0.05)
    fig.tight_layout()
    p = os.path.join(OUT, "fig5_safety_chain_timeline.png")
    fig.savefig(p)
    plt.close(fig)
    print("wrote", p, f"({len(parsed)} layers)")


if __name__ == "__main__":
    fig_environmental(24, "5m", "fig1_environmental_24h.png",
                      "Representative 24-hour cabinet cycle")
    fig_environmental(7 * 24, "1h", "fig2_environmental_7d.png",
                      "Representative 7-day cabinet cycle")
    fig_power()
    fig_pid()
    fig_safety_chain()
    print("done.")
