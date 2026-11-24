#!/usr/bin/env python3
"""Render the website's terrarium charts (last 24 h) straight from InfluxDB.

Replaces the Grafana screenshots on the website. Cron runs it every minute and
writes three PNGs atomically to /home/pi/snapshots/, served by
conditions-server.py under /highland/:
  hero-chart.png        4:3 tile on the highland page
  dashboard-desktop.png the dashboard page, wide layout
  dashboard-mobile.png  the dashboard page, phone layout
"""
import datetime as dt
import json
import os
import tempfile
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as md
import matplotlib.pyplot as plt

TZ = ZoneInfo("Europe/Rome")
OUT_DIR = os.environ.get("HERO_CHART_DIR", "/home/pi/snapshots")

BG, FG, MUTED, GRID, NIGHT = "#111217", "#e8e8ea", "#8a8d98", "#24262d", "#1b2236"
C_T, C_H, C_V, C_ROOM = "#ff9f5a", "#5ab4ff", "#7ddc8c", "#9aa0ad"
C_LIGHT, C_FREEZER, C_MISTER, C_POWER = "#f2c94c", "#4fd1e8", "#b9f08a", "#e8a25a"


def series(meas, agg="mean", every="5m"):
    s = (f'SELECT {agg}("value") FROM "{meas}" WHERE time > now() - 24h '
         f'GROUP BY time({every}) fill(previous)')
    u = "http://127.0.0.1:8086/query?" + urllib.parse.urlencode({"db": "highland", "q": s, "epoch": "s"})
    try:
        v = json.load(urllib.request.urlopen(u, timeout=20))["results"][0]["series"][0]["values"]
    except (KeyError, IndexError, OSError, ValueError):
        return [], []
    pts = [(dt.datetime.fromtimestamp(t, TZ), x) for t, x in v if x is not None]
    return [p[0] for p in pts], [p[1] for p in pts]


def load():
    d = {
        "T": series("local_temperature"), "H": series("local_humidity"), "V": series("vpd"),
        "TT": series("target_temperature_computed"), "TH": series("target_humidity_computed"),
        "RT": series("room_temperature"), "RH": series("room_humidity"),
        "L": series("light_status", "max"), "F": series("freezer_status", "max", "2m"),
        "M": series("mister_status", "max", "1m"),
        "W": series("water_level_local", "last", "15m"), "P": series("power_consumption", "mean", "5m"),
    }
    nights, on = [], None
    for t, x in zip(*d["L"]):
        if x < .5 and on is None:
            on = t
        if x >= .5 and on is not None:
            nights.append((on, t))
            on = None
    if on is not None and d["L"][0]:
        nights.append((on, d["L"][0][-1]))
    d["nights"] = nights
    now = dt.datetime.now(TZ)
    d["xlim"] = (now - dt.timedelta(hours=24), now)   # every panel shares one time axis
    return d


def last(xy, fmt):
    return fmt.format(xy[1][-1]) if xy[1] else "–"


def style_axis(ax, d, ticks=True, size=13):
    ax.set_facecolor(BG)
    for a, b in d["nights"]:
        ax.axvspan(a, b, color=NIGHT, zorder=0, lw=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlim(*d["xlim"])
    if ticks:
        ax.grid(axis="y", color=GRID, lw=.8)
        ax.tick_params(labelsize=size, length=0)
        ax.xaxis.set_major_locator(md.HourLocator(byhour=range(0, 24, 4), tz=TZ))
        ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M", tz=TZ))
    else:
        ax.set_xticks([])


def line_panel(ax, d, xy, color, unit, fmt, title, target=None, room=None, big=30, size=13):
    style_axis(ax, d, size=size)
    if not xy[1]:
        ax.text(.5, .5, "no data", transform=ax.transAxes, ha="center", color=MUTED)
        return
    if room and room[1]:
        ax.plot(*room, color=C_ROOM, lw=1.2, alpha=.7, zorder=2)
    if target and target[1]:
        ax.plot(*target, color=color, lw=1.2, ls=(0, (4, 4)), alpha=.55, zorder=2)
    ax.plot(*xy, color=color, lw=2.2, zorder=3)
    lo, hi = min(xy[1]), max(xy[1])
    y0, y1 = ax.get_ylim()
    ax.fill_between(*xy, y0, color=color, alpha=.10, zorder=1)
    ax.set_ylim(y0, y1)
    ax.text(0, 1.07, title, transform=ax.transAxes, fontsize=size + 3, color=MUTED, va="bottom")
    ax.text(1, 1.06, f"{last(xy, fmt)} {unit}", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=big, color=color, fontweight="bold")
    ax.text(.80 if big >= 30 else .72, 1.07, f"24 h  {fmt.format(lo)} – {fmt.format(hi)}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=size, color=MUTED)


def strip(ax, d, xy, color, name, size=13):
    style_axis(ax, d, ticks=False)
    if xy[1]:
        ax.fill_between(*xy, 0, step="post", color=color, alpha=.85, lw=0)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([])
    ax.text(-.005, .5, name, transform=ax.transAxes, ha="right", va="center", fontsize=size, color=MUTED)


def header(fig, x, y, sub, size=30):
    t = fig.text(x, y, "RORAIMA ", fontsize=size, fontweight="bold", color=FG)
    right = t.get_window_extent(fig.canvas.get_renderer()).x1 / fig.bbox.width
    fig.text(right, y, "· live", fontsize=size, color="#ff5a5f")
    fig.text(x, y - .03, sub, fontsize=size * .47, color=MUTED)


def stat_row(fig, d, y, xs, size=26):
    items = [("Room", last(d["RT"], "{:.1f}") + " °C", C_ROOM), ("Room RH", last(d["RH"], "{:.0f}") + " %", C_ROOM),
             ("Water tank", last(d["W"], "{:.0f}") + " %", C_H), ("Power", last(d["P"], "{:.0f}") + " W", C_POWER)]
    for x, (label, value, color) in zip(xs, items):
        fig.text(x, y + .028, label, fontsize=size * .5, color=MUTED)
        fig.text(x, y, value, fontsize=size, color=color, fontweight="bold")


def save(fig, name):
    out = os.path.join(OUT_DIR, name)
    fd, tmp = tempfile.mkstemp(dir=OUT_DIR, suffix=".png")
    os.close(fd)
    fig.savefig(tmp, facecolor=BG)
    plt.close(fig)
    os.chmod(tmp, 0o644)
    os.replace(tmp, out)


def hero(d):
    fig = plt.figure(figsize=(16, 12), dpi=100, facecolor=BG)
    gs = fig.add_gridspec(5, 1, height_ratios=[3.2, 3.2, 2.4, .55, .55], hspace=.62,
                          left=.06, right=.97, top=.84, bottom=.04)
    line_panel(fig.add_subplot(gs[0]), d, d["T"], C_T, "°C", "{:.1f}", "Temperature", d["TT"])
    line_panel(fig.add_subplot(gs[1]), d, d["H"], C_H, "%", "{:.0f}", "Humidity", d["TH"])
    line_panel(fig.add_subplot(gs[2]), d, d["V"], C_V, "kPa", "{:.2f}", "VPD")
    strip(fig.add_subplot(gs[3]), d, d["F"], C_FREEZER, "Freezer")
    strip(fig.add_subplot(gs[4]), d, d["M"], C_MISTER, "Mister")
    header(fig, .06, .945, "Last 24 h · night shaded · dashed = target")
    save(fig, "hero-chart.png")


def desktop(d):
    fig = plt.figure(figsize=(20, 12), dpi=100, facecolor=BG)
    gs = fig.add_gridspec(3, 2, height_ratios=[3.4, 2.6, .5], hspace=.62, wspace=.16,
                          left=.06, right=.97, top=.72, bottom=.04)
    kw = dict(big=26)
    line_panel(fig.add_subplot(gs[0, 0]), d, d["T"], C_T, "°C", "{:.1f}", "Temperature · room grey", d["TT"], d["RT"], **kw)
    line_panel(fig.add_subplot(gs[0, 1]), d, d["H"], C_H, "%", "{:.0f}", "Humidity · room grey", d["TH"], d["RH"], **kw)
    line_panel(fig.add_subplot(gs[1, 0]), d, d["V"], C_V, "kPa", "{:.2f}", "VPD", **kw)
    line_panel(fig.add_subplot(gs[1, 1]), d, d["P"], C_POWER, "W", "{:.0f}", "Power", **kw)
    strip(fig.add_subplot(gs[2, 0]), d, d["F"], C_FREEZER, "Freezer")   # aligned under its column
    strip(fig.add_subplot(gs[2, 1]), d, d["M"], C_MISTER, "Mister")
    header(fig, .06, .935, "Highland cloud-forest terrarium · Genoa · last 24 h · night shaded · dashed = target", 30)
    stat_row(fig, d, .82, [.06, .26, .46, .66])
    save(fig, "dashboard-desktop.png")


def mobile(d):
    fig = plt.figure(figsize=(9, 18), dpi=100, facecolor=BG)
    gs = fig.add_gridspec(6, 1, height_ratios=[3, 3, 2.2, 2.2, .45, .45], hspace=.75,
                          left=.12, right=.95, top=.81, bottom=.03)
    kw = dict(big=24, size=12)
    line_panel(fig.add_subplot(gs[0]), d, d["T"], C_T, "°C", "{:.1f}", "Temperature", d["TT"], d["RT"], **kw)
    line_panel(fig.add_subplot(gs[1]), d, d["H"], C_H, "%", "{:.0f}", "Humidity", d["TH"], d["RH"], **kw)
    line_panel(fig.add_subplot(gs[2]), d, d["V"], C_V, "kPa", "{:.2f}", "VPD", **kw)
    line_panel(fig.add_subplot(gs[3]), d, d["P"], C_POWER, "W", "{:.0f}", "Power", **kw)
    strip(fig.add_subplot(gs[4]), d, d["F"], C_FREEZER, "Freezer", 12)
    strip(fig.add_subplot(gs[5]), d, d["M"], C_MISTER, "Mister", 12)
    header(fig, .06, .955, "Last 24 h · night shaded · dashed = target · room grey", 28)
    stat_row(fig, d, .875, [.06, .3, .54, .76], size=20)
    save(fig, "dashboard-mobile.png")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": FG, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED})
    data = load()
    for draw in (hero, desktop, mobile):
        draw(data)
